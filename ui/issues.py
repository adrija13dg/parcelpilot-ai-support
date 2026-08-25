"""Operations issues dashboard."""

import streamlit as st

from src.access import SessionContext
from src.config import CUSTOMER_ACCOUNTS
from src.issues import compute_issue_summary


def render_issues(ctx: SessionContext) -> None:
    st.header("Operations Intelligence")

    if not ctx.is_internal:
        st.info("The full operations dashboard is available to Internal Support users.")
        summary = compute_issue_summary()
        account_issues = [
            r
            for r in summary["recurring_issues"]
            if any(
                tid.startswith("TKT")
                for tid in r["ticket_ids"]
            )
        ]
        st.metric("Open issue themes (all customers)", summary["emerging_issues_count"])
        return

    summary = compute_issue_summary()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SLA risk", summary["sla_risk_count"])
    c2.metric("Emerging issues", summary["emerging_issues_count"])
    c3.metric("Recurring themes", summary["recurring_issues_count"])
    c4.metric("Customers affected", summary["customers_affected"])

    st.caption(f"Snapshot: {summary['snapshot_time']}")

    if summary["sla_risk_tickets"]:
        st.subheader("SLA risk tickets")
        for ticket in summary["sla_risk_tickets"]:
            sla = ticket["sla_status"]
            acct = CUSTOMER_ACCOUNTS.get(ticket["account_id"], ticket["account_id"])
            st.markdown(
                f"**{ticket['ticket_id']}** — {acct} — {ticket['subject']}  \n"
                f"Severity {sla['severity']}, elapsed {sla['elapsed_minutes']} min "
                f"(target {sla['target_minutes']} min) — **{'BREACHED' if sla['breached'] else 'Within target'}**"
            )
            if st.button(f"Investigate {ticket['ticket_id']}", key=f"inv_{ticket['ticket_id']}"):
                st.session_state.page = "Chat"
                st.session_state.prefill_question = (
                    f"Analyze ticket {ticket['ticket_id']}: severity, SLA status, and whether we should escalate."
                )
                st.rerun()

    st.subheader("Recurring / emerging themes")
    for issue in summary["recurring_issues"]:
        with st.container(border=True):
            st.markdown(f"### {issue['theme']}")
            st.write(f"{issue['open_count']} open ticket(s), {issue['customers_affected']} customer(s) affected")
            st.caption(f"Tickets: {', '.join(issue['ticket_ids'])}")
            if st.button(f"Investigate: {issue['theme']}", key=f"theme_{issue['theme']}"):
                st.session_state.page = "Chat"
                st.session_state.prefill_question = (
                    f"Investigate the '{issue['theme']}' issue across tickets {', '.join(issue['ticket_ids'])}."
                )
                st.rerun()
