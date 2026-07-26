"""
Embedding package for the GitHub Repository RAG pipeline.

This package provides:
- Formatting AST/document chunks for embedding
- Code-aware embedding providers (Voyage, Qwen, etc.)
- Persistent embedding cache
- High-level embedding manager for batching and orchestration
"""

from .manager import EmbeddingManager

__all__ = ["EmbeddingManager"]