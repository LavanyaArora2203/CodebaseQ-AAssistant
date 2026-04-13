# frontend/components.py

import streamlit as st


# -----------------------------
# CHAT HISTORY DISPLAY
# -----------------------------
def render_chat():
    """Renders full chat history."""

    st.markdown("## 💬 Codebase Q&A")

    if not st.session_state.chat_history:
        st.info("Index a repository from the sidebar, then ask anything about the codebase.")
        return

    for role, message in st.session_state.chat_history:
        if role == "user":
            st.markdown(
                f'<div class="user-msg">🧑 {message}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="bot-msg">🤖 {message}</div>',
                unsafe_allow_html=True
            )


# -----------------------------
# INPUT BOX
# -----------------------------
def render_input_box() -> str:
    """Renders query input. Returns query string or empty string."""

    query = st.chat_input("Ask something about the codebase...")
    return query if query else ""


# -----------------------------
# SOURCE DISPLAY (optional)
# -----------------------------
def render_sources(sources: list):
    """Shows retrieved source chunks in an expander."""

    if not sources:
        return

    with st.expander("📂 Sources used"):
        for i, src in enumerate(sources):
            meta = src.get("metadata", {})
            st.markdown(
                f"**{i+1}. {meta.get('file', 'unknown')}** "
                f"— `{meta.get('type', '')}` "
                f"`{meta.get('function') or meta.get('class') or ''}`"
            )
            with st.expander(f"View code #{i+1}"):
                st.code(src.get("content", ""), language="python")