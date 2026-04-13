import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.title("⚙️ Controls")

        repo_url = st.text_input("GitHub Repo URL")

        ingest_clicked = st.button("Index Repository")

        st.markdown("---")

        if st.button("Clear Chat"):
            st.session_state.chat_history = []

    return repo_url, ingest_clicked