"""Document catalog page."""

import streamlit as st

from src.access import list_accessible_documents
from src.documents import list_available_documents


def render_sources(ctx) -> None:
    st.header("Source Catalog")
    st.caption("Documents ranked by reliability. Lower rank = higher authority.")

    available = {d["filename"]: d for d in list_available_documents()}
    accessible = {d["filename"]: d for d in list_accessible_documents(ctx)}

    for filename, meta in sorted(available.items(), key=lambda x: x[1]["reliability_rank"]):
        acc = accessible[filename]
        status_icon = "✅" if meta["available"] else "⏳"
        access_icon = "🔓" if acc["accessible"] else "🔒"
        st.markdown(
            f"{status_icon} {access_icon} **{meta['title']}** ({meta['doc_type']}, rank {meta['reliability_rank']})"
        )
        st.caption(
            f"File: `{filename}` · Status: {meta['status']} · Scope: {meta['customer_scope']}"
            + (" · **Not uploaded yet**" if not meta["available"] else "")
        )

    st.info(
        "All six assessment documents are indexed. After adding or replacing PDFs in `data/`, run `py scripts/build_index.py`."
    )
