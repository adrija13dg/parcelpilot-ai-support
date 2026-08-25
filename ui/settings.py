"""Settings page."""

import streamlit as st

from src.config import SNAPSHOT_TIME


def render_settings() -> None:
    st.header("Settings")
    st.markdown(f"**Dataset snapshot:** `{SNAPSHOT_TIME.isoformat()}`")
    st.markdown("All SLA and timing calculations use this fixed snapshot.")

    ctx = st.session_state.ctx
    st.markdown(f"**Role:** `{ctx.role}`")
    if ctx.account_name:
        st.markdown(f"**Account:** `{ctx.account_name}` ({ctx.account_id})")

    if st.button("Clear chat history"):
        st.session_state.messages = []
        st.session_state.pending_escalation = None
        st.session_state.last_tool_trace = []
        st.success("Chat cleared.")

    if st.button("Sign out"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
