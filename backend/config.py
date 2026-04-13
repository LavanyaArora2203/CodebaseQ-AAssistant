# backend/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# API KEYS
# -----------------------------
# API KEYS
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# MODELS
LLM_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "text-embedding-3-small"

# -----------------------------
# CHROMA
# -----------------------------
CHROMA_PATH = "backend/chroma_db"
COLLECTION_NAME = "codebase"

# -----------------------------
# INGESTION
# -----------------------------
MAX_FILE_SIZE_MB = 2
CLONE_DIR = "cloned_repo"

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go",
    ".rs", ".md", ".txt", ".json", ".yaml", ".yml", ".html", ".css"
}

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", "venv",
    "env", ".idea", ".vscode", "dist", "build"
}

# -----------------------------
# RETRIEVAL
# -----------------------------
TOP_K = 5