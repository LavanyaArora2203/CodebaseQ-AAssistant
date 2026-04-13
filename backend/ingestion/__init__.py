# backend/ingestion/__init__.py
# Just expose the public API — pipeline logic lives in backend/pipeline.py

from backend.ingestion.repo_loader import load_github_repo
from backend.ingestion.ast_chunker import chunk_documents
from backend.ingestion.metadata_extractor import extract_metadata

__all__ = [
    "load_github_repo",
    "chunk_documents",
    "extract_metadata"
]