"""Role- and account-scoped access control."""

from __future__ import annotations

from dataclasses import dataclass

from src.config import CUSTOMER_ACCOUNTS, DOCUMENT_REGISTRY


@dataclass
class SessionContext:
    role: str  # customer | support_agent
    account_id: str | None = None
    account_name: str | None = None

    @property
    def is_internal(self) -> bool:
        return self.role == "support_agent"


def can_access_account(ctx: SessionContext, account_id: str) -> bool:
    if ctx.is_internal:
        return True
    return ctx.account_id == account_id


def filter_document_metadata(ctx: SessionContext, meta: dict) -> bool:
    scope = meta.get("customer_scope", "global")
    if scope == "global":
        return True
    if ctx.is_internal:
        return True
    return ctx.account_id == scope


def list_accessible_documents(ctx: SessionContext) -> list[dict]:
    docs = []
    for filename, meta in DOCUMENT_REGISTRY.items():
        entry = {"filename": filename, **meta}
        entry["accessible"] = filter_document_metadata(ctx, meta)
        docs.append(entry)
    return docs


def denied_message(entity: str, account_id: str | None = None) -> dict:
    if account_id:
        name = CUSTOMER_ACCOUNTS.get(account_id, account_id)
        return {
            "error": "access_denied",
            "message": f"You do not have permission to access {entity} for {name}.",
        }
    return {"error": "access_denied", "message": f"You do not have permission to access {entity}."}
