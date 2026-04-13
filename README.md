# 🤖 Intelligent Codebase Q&A Assistant

An AI-powered tool that lets you ask natural language questions about any GitHub repository. It uses **RAG (Retrieval-Augmented Generation)** with AST-based code chunking, hybrid search, and an LLM to give accurate, context-aware answers about any codebase.

---
Deployed Link - https://codebase--assistant.streamlit.app/

## 📸 Demo

> Index any GitHub repo → Ask questions → Get intelligent answers with source references

```
Ask: "Where is authentication handled?"
→ FILE: auth/utils.py | FUNCTION: authenticate_user
→ "The authenticate_user function verifies JWT tokens using the verify_token helper..."

Ask: "How does the payment flow work?"
→ FILE: payments/processor.py | CLASS: PaymentProcessor
→ "Payments are handled via the PaymentProcessor class which..."
```

---

## 🧠 How It Works

```
GitHub Repo URL
      ↓
  Clone Repo (GitPython)
      ↓
  AST Chunking (Python ast module)
  → functions, classes, methods with metadata
      ↓
  Store in ChromaDB (vector embeddings)
      ↓
  User Query
      ↓
  Query Classifier → identifies query type
      ↓
  Hybrid Retrieval (Semantic + BM25)
      ↓
  LLM (Groq / llama-3.3-70b) generates answer
      ↓
  Answer + Source Files shown in Streamlit UI
```

---

## 🏗️ Architecture

```
codebase-qa-assistant/
├── backend/
│   ├── ingestion/
│   │   ├── repo_loader.py        # Clone + load repo files
│   │   ├── ast_chunker.py        # AST-based code chunking
│   │   └── metadata_extractor.py # Extract imports, calls, docstrings
│   ├── retrieval/
│   │   ├── vector_store.py       # ChromaDB setup + storage
│   │   ├── hybrid_retriever.py   # Semantic + BM25 hybrid search
│   │   └── query_classifier.py   # Classify query type
│   ├── llm/
│   │   ├── llm_client.py         # Groq API client
│   │   └── prompts.py            # Query-type specific prompts
│   ├── pipeline.py               # Orchestrates full pipeline
│   └── config.py                 # Central configuration
├── frontend/
│   ├── app.py                    # Streamlit entry point
│   ├── components.py             # Chat UI components
│   ├── sidebar.py                # Repo input + controls
│   ├── session_state.py          # Streamlit state management
│   └── styles.css                # Custom styling
├── setup.py
├── requirements.txt
├── .env
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Code Parsing | Python `ast` module |
| Vector Database | ChromaDB |
| Hybrid Search | ChromaDB (semantic) + BM25 (keyword) |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Repo Loading | GitPython |
| Frontend | Streamlit |
| Language | Python 3.11 |

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11 (required — 3.12+ causes compatibility issues with ChromaDB)
- Git
- Groq API key (free at https://console.groq.com)

### Step 1 — Clone this repo
```bash
git clone https://github.com/yourusername/codebase-qa-assistant.git
cd codebase-qa-assistant
```

### Step 2 — Create virtual environment with Python 3.11
```bash
py -3.11 -m venv rag_venv
rag_venv\Scripts\activate       # Windows
# source rag_venv/bin/activate  # Mac/Linux
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

### Step 4 — Set up environment variables
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

### Step 5 — Run the app
```bash
streamlit run frontend/app.py
```

---

## 💡 Usage

1. Open the app in your browser (default: `http://localhost:8501`)
2. Paste any public GitHub repo URL in the sidebar (e.g. `https://github.com/pallets/flask`)
3. Click **Index Repository** and wait for ingestion to complete
4. Ask anything about the codebase in the chat box

### Example Questions
- *"What does the authenticate function do?"*
- *"Where is database connection handled?"*
- *"How do I use the PaymentProcessor class?"*
- *"Why is there an error in the auth module?"*
- *"Explain how the request lifecycle works"*

---

## 🔍 Key Features

**AST-Based Chunking** — Unlike naive text splitting, this tool parses Python files using the Abstract Syntax Tree to extract individual functions, classes, and methods as separate chunks with rich metadata (imports, function calls, docstrings). This gives far more accurate retrieval than character-based chunking.

**Hybrid Retrieval** — Combines semantic vector search (ChromaDB) with keyword-based BM25 search. Semantic search finds conceptually related code while BM25 finds exact function/variable name matches. Results are merged for best coverage.

**Query Classification** — Automatically detects whether you're asking a debugging question, searching for code, asking for usage examples, or requesting an explanation. Each query type uses a tailored prompt for better answers.

**Source References** — Every answer shows exactly which files and functions were used as context, so you can verify and explore further.

---

## 📦 Requirements

```
langchain
langchain-community
langchain-openai
chromadb
rank-bm25
gitpython
streamlit
groq
python-dotenv
pandas
numpy
tqdm
pydantic
tiktoken
setuptools
```

---

## ⚠️ Known Limitations

- Currently optimised for Python repositories (other languages fall back to full-file chunking)
- Large repositories (1000+ files) may take 2-5 minutes to index
- Requires Python 3.11 specifically due to ChromaDB/Pydantic compatibility
- Private repositories require authentication setup in GitPython

---

## 🗺️ Future Improvements

- [ ] Support for JavaScript/TypeScript AST chunking (tree-sitter)
- [ ] Persistent index across sessions (avoid re-indexing same repo)
- [ ] Multi-repo support
- [ ] Streaming answers in UI
- [ ] GitHub PR review assistant mode
- [ ] Docker containerisation

---

## 👤 Author

Built as a portfolio project demonstrating end-to-end RAG pipeline development with ML, vector databases, hybrid search, and LLM integration.

---

## 📄 License

MIT License — free to use and modify.
