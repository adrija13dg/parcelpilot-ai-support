"""FastAPI backend for ParcelPilot AI Support."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.access import SessionContext, list_accessible_documents
from src.agent import run_agent_turn
from src.config import CUSTOMER_ACCOUNTS, SNAPSHOT_TIME
from src.database import init_database
from src.documents import list_available_documents
from src.issues import compute_issue_summary
from src.reliability import compute_reliability
from src.tools import create_escalation

app = FastAPI(title="ParcelPilot AI Support API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_database()


class LoginRequest(BaseModel):
    role: str = Field(..., description="customer or support_agent")
    account_id: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    session: LoginRequest


class EscalationConfirmRequest(BaseModel):
    session: LoginRequest
    ticket_id: str
    reason: str
    severity: str


def session_to_ctx(session: LoginRequest) -> SessionContext:
    account_name = CUSTOMER_ACCOUNTS.get(session.account_id) if session.account_id else None
    return SessionContext(
        role=session.role,
        account_id=session.account_id,
        account_name=account_name,
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "snapshot": SNAPSHOT_TIME.isoformat(),
        "documents_indexed": sum(1 for d in list_available_documents() if d["available"]),
    }


@app.get("/api/accounts")
def accounts():
    return [{"account_id": k, "account_name": v} for k, v in CUSTOMER_ACCOUNTS.items()]


@app.post("/api/session/validate")
def validate_session(session: LoginRequest):
    if session.role == "customer" and not session.account_id:
        raise HTTPException(400, "Customer sessions require account_id")
    if session.account_id and session.account_id not in CUSTOMER_ACCOUNTS:
        raise HTTPException(400, "Invalid account_id")
    ctx = session_to_ctx(session)
    return {
        "role": ctx.role,
        "account_id": ctx.account_id,
        "account_name": ctx.account_name,
        "is_internal": ctx.is_internal,
        "snapshot": SNAPSHOT_TIME.isoformat(),
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    ctx = session_to_ctx(req.session)
    if ctx.role == "customer" and not ctx.account_id:
        raise HTTPException(400, "Customer session requires account")

    messages = [m.model_dump() for m in req.messages]
    try:
        updated, reply, tool_trace, pending = run_agent_turn(messages, ctx)
    except Exception as exc:
        raise HTTPException(500, f"Agent error: {exc}") from exc

    return {
        "reply": reply,
        "messages": updated,
        "tool_trace": tool_trace,
        "pending_escalation": pending,
        "reliability": compute_reliability(tool_trace),
    }


@app.post("/api/escalations/confirm")
def confirm_escalation(req: EscalationConfirmRequest):
    ctx = session_to_ctx(req.session)
    result = create_escalation(req.ticket_id, req.reason, req.severity, ctx)
    if result.get("error"):
        raise HTTPException(403, result.get("message", "Access denied"))
    return result


@app.get("/api/issues")
def issues(role: str = "support_agent", account_id: str | None = None):
    ctx = SessionContext(role=role, account_id=account_id, account_name=CUSTOMER_ACCOUNTS.get(account_id or ""))
    summary = compute_issue_summary()
    if not ctx.is_internal:
        summary["sla_risk_tickets"] = [
            t for t in summary["sla_risk_tickets"] if t["account_id"] == ctx.account_id
        ]
        summary["sla_risk_count"] = len(summary["sla_risk_tickets"])
        summary["customers_affected"] = 1 if summary["sla_risk_tickets"] else 0
    return summary


@app.get("/api/sources")
def sources(role: str = "support_agent", account_id: str | None = None):
    ctx = SessionContext(role=role, account_id=account_id, account_name=CUSTOMER_ACCOUNTS.get(account_id or ""))
    available = list_available_documents()
    accessible = list_accessible_documents(ctx)
    acc_map = {d["filename"]: d for d in accessible}
    return [
        {**doc, "accessible": acc_map.get(doc["filename"], {}).get("accessible", False)}
        for doc in available
    ]


DIST_DIR = ROOT / "frontend" / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(404)
        index = DIST_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        raise HTTPException(404, "Frontend not built. Run: cd frontend && npm install && npm run build")
