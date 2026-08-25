"""Chat page with agent and escalation confirmation."""

import json

import streamlit as st

from src.access import SessionContext
from src.agent import run_agent_turn
from src.tools import create_escalation


def _render_tool_trace(trace: list[dict]) -> None:
    if not trace:
        return
    with st.expander("Tool activity", expanded=False):
        for item in trace:
            st.markdown(f"**{item['tool']}**")
            st.code(json.dumps(item["arguments"], indent=2), language="json")
            st.caption("Result (summary)")
            result = item["result"]
            if isinstance(result, dict) and "results" in result:
                st.write(f"{len(result['results'])} document chunk(s) retrieved")
            elif isinstance(result, dict) and result.get("status") == "pending_confirmation":
                st.write("Escalation prepared — awaiting user confirmation")
            else:
                st.json(result)


def _render_escalation_card(pending: dict, ctx: SessionContext) -> None:
    st.warning("Escalation prepared — confirm to create")
    st.markdown(f"**Ticket:** {pending['ticket_id']}")
    st.markdown(f"**Account:** {pending['account_name']}")
    st.markdown(f"**Severity:** {pending['severity']}")
    st.markdown(f"**Reason:** {pending['reason']}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm escalation", type="primary", key="confirm_esc"):
            result = create_escalation(
                ticket_id=pending["ticket_id"],
                reason=pending["reason"],
                severity=pending["severity"],
                ctx=ctx,
            )
            st.session_state.pending_escalation = None
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Escalation created: **{result['escalation_id']}** for ticket {result['ticket_id']}.",
                }
            )
            st.rerun()
    with col2:
        if st.button("Cancel", key="cancel_esc"):
            st.session_state.pending_escalation = None
            st.session_state.messages.append(
                {"role": "assistant", "content": "Escalation cancelled. No record was created."}
            )
            st.rerun()


def render_chat(ctx: SessionContext) -> None:
    st.header("AI Support Agent")
    st.caption(f"Session: {'Internal Support' if ctx.is_internal else ctx.account_name}")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_escalation" not in st.session_state:
        st.session_state.pending_escalation = None
    if "last_tool_trace" not in st.session_state:
        st.session_state.last_tool_trace = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.pending_escalation:
        _render_escalation_card(st.session_state.pending_escalation, ctx)

    if st.session_state.last_tool_trace:
        _render_tool_trace(st.session_state.last_tool_trace)

    prefilled = st.session_state.pop("prefill_question", None)
    prompt = st.chat_input("Ask about orders, tickets, policies, or escalations...")
    user_text = prefilled or prompt

    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    updated, reply, trace, pending = run_agent_turn(st.session_state.messages, ctx)
                    st.session_state.messages = [
                        m for m in updated if m["role"] in ("user", "assistant") and m.get("content")
                    ]
                    st.session_state.last_tool_trace = trace
                    st.session_state.pending_escalation = pending
                    st.markdown(reply)
                    _render_tool_trace(trace)
                except Exception as exc:
                    st.error(f"Agent error: {exc}")

        st.rerun()
