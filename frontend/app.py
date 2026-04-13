import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from frontend.components import render_chat, render_input_box, render_sources

import streamlit as st
from backend.pipeline import ingest_repo, RAGPipeline
# rest of imports...


from frontend.sidebar import render_sidebar
from frontend.components import render_chat, render_input_box
from frontend.session_state import init_session_state

# -----------------------------
# INIT
# -----------------------------
st.set_page_config(page_title="Codebase Q&A Assistant", layout="wide")

init_session_state()

# Load CSS
with open("frontend/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# -----------------------------
# SIDEBAR
# -----------------------------
repo_url, ingest_clicked = render_sidebar()

# -----------------------------
# INGESTION
# -----------------------------
if ingest_clicked and repo_url:
    with st.spinner("Indexing repository..."):
        chunks = ingest_repo(repo_url)
        st.session_state.chunks = chunks
        st.session_state.rag = RAGPipeline(chunks)

    st.success("Repository indexed successfully!")

# -----------------------------
# CHAT UI
# -----------------------------
render_chat()

# -----------------------------
# USER INPUT
# -----------------------------
query = render_input_box()

# in app.py, replace the query block with this:
if query:
    st.session_state.chat_history.append(("user", query))

    if st.session_state.rag:
        with st.spinner("Thinking..."):
            result = st.session_state.rag.run(query)
            answer = result["answer"]
            sources = result["sources"]          # ✅ grab sources

        st.session_state.chat_history.append(("assistant", answer))
        render_sources(sources)                  # ✅ show sources
    else:
        st.warning("Please index a repository first.")