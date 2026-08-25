"""Answer reliability scoring from tool results."""

from __future__ import annotations


def compute_reliability(tool_trace: list[dict]) -> dict:
    """
    Score each answer high / medium / low based on sources actually used.
    """
    if not tool_trace:
        return {
            "level": "low",
            "label": "Low reliability",
            "reasons": ["No tools were used to verify this answer."],
        }

    reasons: list[str] = []
    has_agreement = False
    has_current_policy = False
    has_sop_or_product = False
    has_deprecated = False
    has_operational = False
    access_denied = False
    used_historical = False
    missing_doc_note = False

    for item in tool_trace:
        tool = item.get("tool", "")
        result = item.get("result") or {}

        if result.get("error") == "access_denied":
            access_denied = True
            reasons.append("Some data was correctly withheld by access control.")

        if tool == "search_documents":
            for doc in result.get("results", []):
                status = doc.get("status", "current")
                doc_type = doc.get("doc_type", "")
                title = doc.get("title", doc.get("source_file", "document"))
                if status == "deprecated":
                    has_deprecated = True
                    reasons.append(f"Retrieved deprecated source: {title}")
                elif doc_type == "agreement":
                    has_agreement = True
                    reasons.append(f"Signed agreement: {title}")
                elif doc_type == "policy":
                    has_current_policy = True
                    reasons.append(f"Current policy: {title}")
                elif doc_type in ("sop", "product_guide"):
                    has_sop_or_product = True
                    reasons.append(f"Operational doc: {title}")
            if not result.get("results"):
                missing_doc_note = True
                reasons.append("Required document may be missing from search results.")

        if tool == "query_operational_data":
            has_operational = True
            entity = result.get("entity", "record")
            if result.get("cancellation_assessment"):
                ca = result["cancellation_assessment"]
                if ca.get("conflict_warning"):
                    used_historical = True
                    reasons.append("Historical ticket conflict detected and flagged.")
                reasons.append(f"Operational assessment on {entity}.")
            elif result.get("sla_status"):
                reasons.append("SLA computed from live ticket data.")
            elif result.get("failed_pickup_credit"):
                reasons.append("Credit eligibility computed from order data.")
            else:
                reasons.append(f"Operational lookup: {entity}.")

        if tool == "prepare_escalation":
            reasons.append("Escalation prepared — pending user confirmation.")

    # Determine level
    if access_denied and not has_operational and not has_agreement:
        level = "high"
        label = "High reliability"
    elif has_agreement or (has_operational and (has_current_policy or has_sop_or_product)):
        level = "high"
        label = "High reliability"
    elif has_operational or has_current_policy or has_sop_or_product:
        level = "medium"
        label = "Medium reliability"
    elif has_deprecated and not has_agreement and not has_current_policy:
        level = "low"
        label = "Low reliability"
    elif used_historical or missing_doc_note or not has_operational:
        level = "low" if (used_historical or missing_doc_note) else "medium"
        label = "Low reliability" if level == "low" else "Medium reliability"
    else:
        level = "medium"
        label = "Medium reliability"

    if has_deprecated and level == "high":
        level = "medium"
        label = "Medium reliability"
        reasons.append("Deprecated document retrieved — current sources should take precedence.")

    # Dedupe reasons while preserving order
    seen: set[str] = set()
    unique_reasons = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique_reasons.append(r)

    if not unique_reasons:
        unique_reasons = ["Answer based on tool results."]

    return {"level": level, "label": label, "reasons": unique_reasons[:6]}
