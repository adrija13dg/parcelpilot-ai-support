"""Operations intelligence dashboard — Ops Radar."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from src.business_logic import assess_ticket_sla, row_to_dict
from src.config import CUSTOMER_ACCOUNTS, SNAPSHOT_TIME
from src.database import fetch_all

KNOWN_ISSUES = {
    "KI-208": {
        "title": "Bulk Upload failures on large CSVs",
        "status": "Investigating",
        "keywords": ["bulk upload", "csv", "upload fail"],
        "workaround": "Split uploads below 3,000 rows per file.",
    },
    "KI-211": {
        "title": "SwiftShip pickup webhook delay",
        "status": "Monitoring",
        "keywords": ["swiftship", "still shows booked", "booked after", "pickup webhook"],
        "workaround": "Wait up to 20 minutes or verify carrier status before telling customer pickup failed.",
    },
}


def _theme(subject: str, description: str) -> str:
    text = f"{subject} {description}".lower()
    if "bulk upload" in text or "csv" in text:
        return "Bulk upload failures"
    if "http 500" in text or "shipment creation" in text:
        return "Shipment creation outage"
    if "booked after" in text or "still shows booked" in text:
        return "Carrier status sync delay"
    if "api key" in text or "credential" in text:
        return "Credential exposure"
    if "cancellation" in text or "cancel" in text:
        return "Cancellation fee disputes"
    if "billing contact" in text:
        return "Account admin requests"
    return "Other support issues"


def _normalize_subject(subject: str) -> str:
    s = subject.lower()
    s = re.sub(r"\d+", "#", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _match_known_issues(ticket: dict) -> list[str]:
    text = f"{ticket['subject']} {ticket['description']}".lower()
    matched = []
    for ki_id, ki in KNOWN_ISSUES.items():
        if any(kw in text for kw in ki["keywords"]):
            matched.append(ki_id)
    return matched


def compute_issue_summary() -> dict:
    tickets = [row_to_dict(r) for r in fetch_all("SELECT * FROM tickets")]
    open_tickets = [t for t in tickets if t["status"] == "open"]
    closed_tickets = [t for t in tickets if t["status"] == "closed"]

    sla_risk = []
    themes_open: Counter[str] = Counter()
    themes_closed: Counter[str] = Counter()
    affected_accounts: set[str] = set()

    for ticket in open_tickets:
        sla = assess_ticket_sla(ticket)
        if sla.get("recommend_escalation"):
            sla_risk.append({**ticket, "sla_status": sla})
        theme = _theme(ticket["subject"], ticket["description"])
        themes_open[theme] += 1
        affected_accounts.add(ticket["account_id"])

    for ticket in closed_tickets:
        themes_closed[_theme(ticket["subject"], ticket["description"])] += 1

    recurring = []
    for theme, count in themes_open.most_common():
        related = [t for t in open_tickets if _theme(t["subject"], t["description"]) == theme]
        accts = {t["account_id"] for t in related}
        recurring.append(
            {
                "theme": theme,
                "open_count": count,
                "customers_affected": len(accts),
                "ticket_ids": [t["ticket_id"] for t in related],
                "sample_subject": related[0]["subject"] if related else "",
            }
        )

    # Duplicate / similar ticket clusters (open + recent closed with similar subject)
    subject_groups: dict[str, list[dict]] = defaultdict(list)
    for t in tickets:
        key = _normalize_subject(t["subject"])
        subject_groups[key].append(t)

    duplicate_clusters = []
    for key, group in subject_groups.items():
        if len(group) < 2:
            continue
        open_ids = [t["ticket_id"] for t in group if t["status"] == "open"]
        if not open_ids:
            continue
        duplicate_clusters.append(
            {
                "cluster_key": key,
                "sample_subject": group[0]["subject"],
                "ticket_ids": [t["ticket_id"] for t in group],
                "open_count": len(open_ids),
                "accounts": list({CUSTOMER_ACCOUNTS.get(t["account_id"], t["account_id"]) for t in group}),
                "statuses": [t["status"] for t in group],
            }
        )

    # Category volume spikes (open vs closed baseline in this snapshot)
    volume_spikes = []
    all_themes = set(themes_open.keys()) | set(themes_closed.keys())
    for theme in all_themes:
        open_n = themes_open.get(theme, 0)
        closed_n = themes_closed.get(theme, 0)
        if open_n >= 1 and open_n > closed_n:
            pct = int(((open_n - closed_n) / max(closed_n, 1)) * 100)
            volume_spikes.append(
                {
                    "theme": theme,
                    "open_count": open_n,
                    "closed_baseline": closed_n,
                    "spike_pct": pct,
                    "severity": "high" if pct >= 100 else "medium",
                }
            )
    volume_spikes.sort(key=lambda x: x["spike_pct"], reverse=True)

    # Known issue matches
    known_issue_matches = []
    for ki_id, ki in KNOWN_ISSUES.items():
        matched_tickets = [t for t in open_tickets if ki_id in _match_known_issues(t)]
        if matched_tickets:
            known_issue_matches.append(
                {
                    "known_issue_id": ki_id,
                    "title": ki["title"],
                    "status": ki["status"],
                    "workaround": ki["workaround"],
                    "ticket_ids": [t["ticket_id"] for t in matched_tickets],
                    "customers_affected": len({t["account_id"] for t in matched_tickets}),
                }
            )

    return {
        "snapshot_time": SNAPSHOT_TIME.isoformat(),
        "sla_risk_count": len(sla_risk),
        "sla_risk_tickets": sla_risk,
        "emerging_issues_count": len(recurring),
        "recurring_issues_count": len(recurring),
        "customers_affected": len(affected_accounts),
        "recurring_issues": recurring,
        "duplicate_clusters": duplicate_clusters,
        "volume_spikes": volume_spikes,
        "known_issue_matches": known_issue_matches,
        "duplicate_cluster_count": len(duplicate_clusters),
        "volume_spike_count": len(volume_spikes),
        "known_issue_count": len(known_issue_matches),
    }
