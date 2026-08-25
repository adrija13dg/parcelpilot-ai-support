"""Agent tool implementations."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from src.access import SessionContext, can_access_account, denied_message
from src.business_logic import (
    assess_cancellation,
    assess_failed_pickup_credit,
    assess_ticket_sla,
    row_to_dict,
)
from src.config import CUSTOMER_ACCOUNTS, SNAPSHOT_TIME
from src.database import execute, fetch_all, fetch_one
from src.rag import get_document_index


def search_documents(query: str, ctx: SessionContext, doc_types: list[str] | None = None) -> dict:
    results = get_document_index().search(query, ctx, top_k=5)
    if doc_types:
        results = [r for r in results if r["doc_type"] in doc_types]

    return {
        "query": query,
        "results": results,
        "precedence_note": (
            "When sources conflict: signed customer agreement first, then current support policy, "
            "then SOP/product docs. Historical ticket resolutions are context only and may be incorrect."
        ),
    }


def query_operational_data(
    entity: str,
    identifier: str,
    ctx: SessionContext,
    action: str = "lookup",
) -> dict:
    entity = entity.lower().strip()
    identifier = identifier.strip()

    if entity == "account":
        row = fetch_one(
            "SELECT * FROM accounts WHERE account_id = ? OR account_name = ? COLLATE NOCASE",
            (identifier, identifier),
        )
        if not row:
            return {"error": "not_found", "message": f"Account '{identifier}' not found."}
        if not can_access_account(ctx, row["account_id"]):
            return denied_message("account data", row["account_id"])
        return {"entity": "account", "data": row_to_dict(row)}

    if entity == "order":
        row = fetch_one("SELECT * FROM orders WHERE order_id = ?", (identifier,))
        if not row:
            return {"error": "not_found", "message": f"Order '{identifier}' not found."}
        if not can_access_account(ctx, row["account_id"]):
            return denied_message("order data", row["account_id"])
        account = fetch_one("SELECT * FROM accounts WHERE account_id = ?", (row["account_id"],))
        data = row_to_dict(row)
        payload: dict = {"entity": "order", "data": data, "account": row_to_dict(account)}

        if action == "cancellation_assessment":
            payload["cancellation_assessment"] = assess_cancellation(data, row_to_dict(account))
        elif action == "failed_pickup_credit":
            payload["failed_pickup_credit"] = assess_failed_pickup_credit(data, row_to_dict(account))
        return payload

    if entity == "ticket":
        row = fetch_one("SELECT * FROM tickets WHERE ticket_id = ?", (identifier,))
        if not row:
            return {"error": "not_found", "message": f"Ticket '{identifier}' not found."}
        if not can_access_account(ctx, row["account_id"]):
            return denied_message("ticket data", row["account_id"])
        data = row_to_dict(row)
        payload = {"entity": "ticket", "data": data}
        if action in ("lookup", "sla_status"):
            payload["sla_status"] = assess_ticket_sla(data)
        return payload

    if entity == "orders_by_account":
        account = fetch_one(
            "SELECT * FROM accounts WHERE account_id = ? OR account_name = ? COLLATE NOCASE",
            (identifier, identifier),
        )
        if not account:
            return {"error": "not_found", "message": f"Account '{identifier}' not found."}
        if not can_access_account(ctx, account["account_id"]):
            return denied_message("orders", account["account_id"])
        rows = fetch_all("SELECT * FROM orders WHERE account_id = ?", (account["account_id"],))
        return {"entity": "orders", "account": row_to_dict(account), "data": [row_to_dict(r) for r in rows]}

    if entity == "tickets_by_account":
        account = fetch_one(
            "SELECT * FROM accounts WHERE account_id = ? OR account_name = ? COLLATE NOCASE",
            (identifier, identifier),
        )
        if not account:
            return {"error": "not_found", "message": f"Account '{identifier}' not found."}
        if not can_access_account(ctx, account["account_id"]):
            return denied_message("tickets", account["account_id"])
        rows = fetch_all("SELECT * FROM tickets WHERE account_id = ?", (account["account_id"],))
        return {"entity": "tickets", "account": row_to_dict(account), "data": [row_to_dict(r) for r in rows]}

    return {"error": "invalid_entity", "message": f"Unknown entity '{entity}'."}


def prepare_escalation(
    ticket_id: str,
    reason: str,
    severity: str,
    ctx: SessionContext,
) -> dict:
    ticket = fetch_one("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    if not ticket:
        return {"error": "not_found", "message": f"Ticket '{ticket_id}' not found."}
    if not can_access_account(ctx, ticket["account_id"]):
        return denied_message("ticket escalation", ticket["account_id"])

    sla = assess_ticket_sla(row_to_dict(ticket))
    account = fetch_one("SELECT account_name FROM accounts WHERE account_id = ?", (ticket["account_id"],))

    return {
        "status": "pending_confirmation",
        "ticket_id": ticket_id,
        "account_id": ticket["account_id"],
        "account_name": account["account_name"] if account else ticket["account_id"],
        "severity": severity,
        "reason": reason,
        "sla_status": sla,
        "message": "Escalation prepared. User must confirm before it is created.",
    }


def create_escalation(
    ticket_id: str,
    reason: str,
    severity: str,
    ctx: SessionContext,
) -> dict:
    ticket = fetch_one("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    if not ticket:
        return {"error": "not_found", "message": f"Ticket '{ticket_id}' not found."}
    if not can_access_account(ctx, ticket["account_id"]):
        return denied_message("ticket escalation", ticket["account_id"])

    escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    created_at = SNAPSHOT_TIME.isoformat()
    execute(
        """
        INSERT INTO escalations (escalation_id, ticket_id, account_id, severity, reason, created_at, created_by_role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (escalation_id, ticket_id, ticket["account_id"], severity, reason, created_at, ctx.role),
    )
    return {
        "status": "created",
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "account_id": ticket["account_id"],
        "severity": severity,
        "reason": reason,
        "created_at": created_at,
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search ParcelPilot policies, SOPs, agreements, and product docs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query."},
                    "doc_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional filter: policy, sop, agreement, product_guide.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_operational_data",
            "description": "Look up accounts, orders, tickets, or run assessments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "enum": [
                            "account",
                            "order",
                            "ticket",
                            "orders_by_account",
                            "tickets_by_account",
                        ],
                    },
                    "identifier": {"type": "string", "description": "ID or account name."},
                    "action": {
                        "type": "string",
                        "enum": ["lookup", "cancellation_assessment", "failed_pickup_credit", "sla_status"],
                        "description": "Optional action for order/ticket entities.",
                    },
                },
                "required": ["entity", "identifier"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_escalation",
            "description": "Prepare a ticket escalation for user confirmation. Does NOT create it yet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "severity": {"type": "string", "enum": ["P1", "P2", "P3"]},
                },
                "required": ["ticket_id", "reason", "severity"],
            },
        },
    },
]


def dispatch_tool(name: str, arguments: dict, ctx: SessionContext) -> dict:
    if name == "search_documents":
        return search_documents(
            query=arguments["query"],
            ctx=ctx,
            doc_types=arguments.get("doc_types"),
        )
    if name == "query_operational_data":
        return query_operational_data(
            entity=arguments["entity"],
            identifier=arguments["identifier"],
            ctx=ctx,
            action=arguments.get("action", "lookup"),
        )
    if name == "prepare_escalation":
        return prepare_escalation(
            ticket_id=arguments["ticket_id"],
            reason=arguments["reason"],
            severity=arguments["severity"],
            ctx=ctx,
        )
    return {"error": "unknown_tool", "message": f"Tool '{name}' is not available."}
