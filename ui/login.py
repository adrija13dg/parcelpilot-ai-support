"""Login screen."""

import streamlit as st

from src.access import SessionContext
from src.config import CUSTOMER_ACCOUNTS


def render_login() -> None:
    st.title("ParcelPilot Support Portal")
    st.caption("Mock login for role-based access control demo")

    role = st.radio("Role", ["Customer", "Internal Support"], horizontal=True)
    account_id = None
    account_name = None

    if role == "Customer":
        account_name = st.selectbox("Account", list(CUSTOMER_ACCOUNTS.values()))
        account_id = next(k for k, v in CUSTOMER_ACCOUNTS.items() if v == account_name)

    if st.button("Continue", type="primary", use_container_width=True):
        st.session_state.authenticated = True
        st.session_state.ctx = SessionContext(
            role="support_agent" if role == "Internal Support" else "customer",
            account_id=account_id,
            account_name=account_name,
        )
        st.session_state.page = "Chat"
        st.rerun()
