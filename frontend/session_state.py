import streamlit as st


def init_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "chunks" not in st.session_state:
        st.session_state.chunks = None

    if "rag" not in st.session_state:
        st.session_state.rag = None