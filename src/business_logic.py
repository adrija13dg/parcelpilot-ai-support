"""Operational calculations: SLA, cancellation, credits, severity."""

from __future__ import annotations

from datetime import datetime

from src.config import (
    DEFAULT_SLA_TARGETS,
    LUMENWORKS_SLA_TARGETS,
    NORTHSTAR_SLA_TARGETS,
    SNAPSHOT_TIME,
)
from src.database import fetch_one


def parse_dt(value: str | None) -> datetime | None:
    if not value or (isinstance(value, float) and str(value) == "nan"):
        return None
    dt = datetime.fromisoformat(str(value).replace(" ", "T"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=SNAPSHOT_TIME.tzinfo)
    return dt


def minutes_between(start: datetime | None, end: datetime | None) -> int | None:
    if not start or not end:
        return None
    return int((end - start).total_seconds() // 60)


def get_sla_targets(account_id: str, plan: str) -> dict[str, int]:
    if account_id == "ACCT-001":
        return NORTHSTAR_SLA_TARGETS.copy()
    if account_id == "ACCT-002":
        return LUMENWORKS_SLA_TARGETS.copy()
    return DEFAULT_SLA_TARGETS.get(plan, DEFAULT_SLA_TARGETS["Standard"]).copy()


def classify_severity(subject: str, description: str) -> str:
    text = f"{subject} {description}".lower()
    p1_signals = [
        "http 500",
        "all shipment creation",
        "api key",
        "credential",
        "security incident",
        "complete production outage",
    ]
    p2_signals = [
        "bulk upload",
        "still shows booked",
        "major feature",
        "workaround",
        "degraded",
    ]
    if any(s in text for s in p1_signals):
        return "P1"
    if any(s in text for s in p2_signals):
        return "P2"
    return "P3"


def assess_ticket_sla(ticket_row: dict) -> dict:
    account = fetch_one("SELECT * FROM accounts WHERE account_id = ?", (ticket_row["account_id"],))
    if not account:
        return {"error": "account_not_found"}

    severity = classify_severity(ticket_row["subject"], ticket_row["description"])
    targets = get_sla_targets(account["account_id"], account["plan"])
    target_minutes = targets[severity]
    created = parse_dt(ticket_row["created_at"])
    elapsed = minutes_between(created, SNAPSHOT_TIME)
    breached = elapsed is not None and elapsed > target_minutes

    return {
        "ticket_id": ticket_row["ticket_id"],
        "account_id": ticket_row["account_id"],
        "account_name": account["account_name"],
        "severity": severity,
        "target_minutes": target_minutes,
        "elapsed_minutes": elapsed,
        "breached": breached,
        "snapshot_time": SNAPSHOT_TIME.isoformat(),
        "recommend_escalation": severity == "P1" or breached,
    }


def assess_cancellation(order_row: dict, account_row: dict) -> dict:
    status = order_row["status"]
    account_id = account_row["account_id"]
    booked_at = parse_dt(order_row["booked_at"])
    cancel_at = parse_dt(order_row.get("cancellation_requested_at"))
    minutes_since_booking = minutes_between(booked_at, cancel_at or SNAPSHOT_TIME)

    result = {
        "order_id": order_row["order_id"],
        "account_id": account_id,
        "account_name": account_row["account_name"],
        "status": status,
        "minutes_since_booking": minutes_since_booking,
        "cancellation_requested_at": order_row.get("cancellation_requested_at"),
    }

    if status == "DELIVERED":
        result.update(
            {
                "can_cancel": False,
                "fee_inr": None,
                "rationale": "Order is already delivered.",
                "sources": ["operational_data"],
            }
        )
        return result

    if status == "PICKED_UP":
        result.update(
            {
                "can_cancel_without_fee": False,
                "fee_inr": None,
                "rationale": "Shipment already picked up. Use return-to-origin workflow per SOP v4.",
                "sources": ["03_Cancellation_and_Service_Credit_SOP_v4.pdf"],
            }
        )
        return result

    if account_id == "ACCT-001" and status == "BOOKED":
        result.update(
            {
                "can_cancel_without_fee": True,
                "fee_inr": 0,
                "rationale": "Northstar agreement allows free cancellation of BOOKED shipments before pickup, regardless of booking age.",
                "sources": ["05_Northstar_Logistics_Enterprise_Agreement.pdf"],
                "conflict_warning": "Historical ticket TKT-450 suggested INR 250 fee after 30 minutes — that guidance is incorrect per the signed agreement.",
            }
        )
        return result

    if status == "BOOKED":
        sop_free_window = minutes_since_booking is not None and minutes_since_booking <= 30
        fee = 0 if sop_free_window else 250
        result.update(
            {
                "can_cancel_without_fee": sop_free_window,
                "fee_inr": fee,
                "rationale": (
                    "SOP v4: no fee within 30 minutes of booking for BOOKED shipments."
                    if sop_free_window
                    else "SOP v4: INR 250 cancellation fee applies after 30 minutes (no agreement waiver)."
                ),
                "sources": ["03_Cancellation_and_Service_Credit_SOP_v4.pdf"],
            }
        )
        return result

    result.update(
        {
            "can_cancel_without_fee": None,
            "fee_inr": None,
            "rationale": "Unable to assess cancellation for this order status.",
            "sources": ["03_Cancellation_and_Service_Credit_SOP_v4.pdf"],
        }
    )
    return result


def assess_failed_pickup_credit(order_row: dict, account_row: dict) -> dict:
    account_id = account_row["account_id"]
    window_end = parse_dt(order_row["pickup_window_end"])
    hours_late = None
    if window_end:
        hours_late = (SNAPSHOT_TIME - window_end).total_seconds() / 3600

    eligible_lumenworks = (
        account_id == "ACCT-002"
        and order_row["carrier_fault"]
        and not order_row["customer_fault"]
        and hours_late is not None
        and hours_late > 4
        and order_row["status"] == "BOOKED"
    )

    if eligible_lumenworks:
        return {
            "order_id": order_row["order_id"],
            "eligible": True,
            "credit_inr": 300,
            "hours_past_window_end": round(hours_late, 2),
            "rationale": "LumenWorks agreement provides INR 300 credit when pickup is >4 hours past window end with carrier at fault.",
            "sources": ["06_LumenWorks_Service_Agreement.pdf"],
        }

    eligible_sop = (
        order_row["carrier_fault"]
        and not order_row["customer_fault"]
        and hours_late is not None
        and hours_late > 2
        and order_row["status"] == "BOOKED"
    )
    if eligible_sop:
        shipment_fee = int(order_row["shipment_fee_inr"])
        credit = min(500, int(shipment_fee * 0.10))
        return {
            "order_id": order_row["order_id"],
            "eligible": True,
            "credit_inr": credit,
            "hours_past_window_end": round(hours_late, 2),
            "rationale": "SOP v4 default: credit is lower of INR 500 or 10% of shipment fee when pickup is >2 hours past window end with carrier at fault.",
            "sources": ["03_Cancellation_and_Service_Credit_SOP_v4.pdf"],
        }

    return {
        "order_id": order_row["order_id"],
        "eligible": False,
        "credit_inr": 0,
        "hours_past_window_end": round(hours_late, 2) if hours_late is not None else None,
        "rationale": "Failed-pickup credit thresholds not met, or a customer agreement overrides default SOP rules.",
        "sources": ["03_Cancellation_and_Service_Credit_SOP_v4.pdf", "06_LumenWorks_Service_Agreement.pdf"],
    }


def row_to_dict(row) -> dict:
    return dict(row) if row else {}
