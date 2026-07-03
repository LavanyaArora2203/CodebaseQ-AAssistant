#!/usr/bin/env python3
"""
embeddings.py

Turns chunk text into vectors, in batches, and pairs each vector with its
chunk's metadata so the two travel together into the vector store.

Two embedders are provided behind one interface (`Embedder`):

    SentenceTransformerEmbedder
        Wraps a real neural embedding model via `sentence-transformers`.
        This is what you want for production use. Pick the model based on
        what you're embedding:
          - code-aware:      "flax-sentence-embeddings/st-codesearch-distilroberta-base"
                              or "jinaai/jina-embeddings-v2-base-code"
          - general-purpose: "BAAI/bge-small-en-v1.5" (small, fast, strong)
                              or "sentence-transformers/all-MiniLM-L6-v2"
        Since our chunks are a mix of Python (function/class/docstring/
        comment) and Markdown (markdown_section), a general-purpose model
        is the safer default — code-aware models are tuned for
        code<->natural-language-query retrieval specifically and can
        underperform on prose-heavy chunks like docstrings and markdown.
        Downloads the model from Hugging Face on first use, so it needs
        outbound network access.

    LocalHashingEmbedder
        A dependency-light, fully offline fallback: TF-IDF over character
        n-grams, hashed and dimensionality-reduced with truncated SVD, fit
        once across the corpus being embedded. No model download, fully
        deterministic. It's meaningfully worse at semantic similarity than
        a real embedding model, but keeps this module runnable in
        network-restricted environments (like this sandbox) and is fine
        for smoke-testing the pipeline end to end.

Both implement:
    embed(texts: list[str]) -> np.ndarray of shape (len(texts), dim)

and batch internally.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

# ts_chunker.Chunk has: file_path, chunk_type, name, qualified_name,
# start_line, end_line, parent_class, parent_function, language,
# part_index, total_parts, source
from ts_chunker import Chunk


@dataclass
class EmbeddedChunk:
    """A chunk's vector, paired with its full metadata, ready to insert."""
    id: str
    vector: np.ndarray
    text: str
    metadata: dict


class Embedder(ABC):
    name: str = "base"
    dim: int = 0

    @abstractmethod
    def embed(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        ...

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]


# --------------------------------------------------------------------------
# Real embedder: sentence-transformers
# --------------------------------------------------------------------------

class SentenceTransformerEmbedder(Embedder):
    """
    General-purpose or code-aware embedding via sentence-transformers.

    Default model is general-purpose (bge-small) rather than code-specific,
    since our corpus mixes source code with docstrings/comments/markdown
    prose. Pass a code-aware model name if your corpus is code-dominant and
    queries will mostly be code<->code or code<->short-query lookups.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: Optional[str] = None):
        from sentence_transformers import SentenceTransformer  # deferred import
        self.name = model_name
        self._model = SentenceTransformer(model_name, device=device)
        self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        vectors = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,  # cosine similarity via dot product
            convert_to_numpy=True,
        )
        return vectors.astype("float32")


# --------------------------------------------------------------------------
# Offline fallback embedder: hashed TF-IDF + SVD
# --------------------------------------------------------------------------

class LocalHashingEmbedder(Embedder):
    """
    Deterministic, dependency-light embedder requiring no model download.
    Fits a TF-IDF vectorizer (char n-grams, so it degrades gracefully on
    code identifiers/punctuation) and reduces to `dim` dimensions with
    truncated SVD. Must be fit once on a representative batch (typically
    the full corpus you're about to index) before embedding queries.
    """

    def __init__(self, dim: int = 256):
        self.name = f"local-hashing-tfidf-svd-{dim}"
        self.dim = dim
        self._fitted = False
        self._vectorizer = None
        self._svd = None

    def fit(self, texts: List[str]) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), max_features=20000
        )
        tfidf = self._vectorizer.fit_transform(texts)

        n_components = min(self.dim, max(1, tfidf.shape[0] - 1), tfidf.shape[1] - 1)
        self._svd = TruncatedSVD(n_components=n_components, random_state=0)
        self._svd.fit(tfidf)
        self.dim = n_components
        self._fitted = True

    def embed(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        if not self._fitted:
            # Fit-on-first-use so this class is a drop-in Embedder even if
            # the caller doesn't fit() explicitly. For best results, call
            # fit() once on the full corpus before embedding queries.
            self.fit(texts)

        tfidf = self._vectorizer.transform(texts)
        vectors = self._svd.transform(tfidf).astype("float32")
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms  # normalize for cosine similarity via dot product

    def save(self, path: str) -> None:
        """Persist the fitted vectorizer + SVD so queries can reuse the same
        vector space in a later process, without re-fitting on the corpus."""
        import pickle
        if not self._fitted:
            raise RuntimeError("Cannot save an unfitted LocalHashingEmbedder; call fit() or embed() first.")
        with open(path, "wb") as f:
            pickle.dump({"dim": self.dim, "vectorizer": self._vectorizer, "svd": self._svd}, f)

    @classmethod
    def load(cls, path: str) -> "LocalHashingEmbedder":
        import pickle
        with open(path, "rb") as f:
            state = pickle.load(f)
        embedder = cls(dim=state["dim"])
        embedder._vectorizer = state["vectorizer"]
        embedder._svd = state["svd"]
        embedder._fitted = True
        return embedder


# --------------------------------------------------------------------------
# Batch embedding of Chunk objects
# --------------------------------------------------------------------------

def _chunk_id(chunk: Chunk) -> str:
    """Stable id: file + qualified name/type + line range + part index."""
    key = f"{chunk.file_path}:{chunk.qualified_name or chunk.name or chunk.chunk_type}:{chunk.start_line}-{chunk.end_line}:{chunk.part_index or 0}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def _chunk_metadata(chunk: Chunk) -> dict:
    return {
        "file_path": chunk.file_path,
        "chunk_type": chunk.chunk_type,
        "name": chunk.name,
        "qualified_name": chunk.qualified_name,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "parent_class": chunk.parent_class,
        "parent_function": chunk.parent_function,
        "language": chunk.language,
        "part_index": chunk.part_index,
        "total_parts": chunk.total_parts,
    }


def batch_embed_chunks(chunks: List[Chunk], embedder: Embedder, batch_size: int = 32) -> List[EmbeddedChunk]:
    """
    Embed a list of Chunk objects in batches and pair each resulting vector
    with the chunk's text and metadata.
    """
    if not chunks:
        return []

    texts = [c.source for c in chunks]

    # LocalHashingEmbedder needs a fit pass; fit it on this exact corpus so
    # queries embedded later (via the same embedder instance) share the
    # same vector space.
    if isinstance(embedder, LocalHashingEmbedder) and not embedder._fitted:
        embedder.fit(texts)

    vectors = embedder.embed(texts, batch_size=batch_size)

    embedded = []
    for chunk, vector, text in zip(chunks, vectors, texts):
        embedded.append(EmbeddedChunk(
            id=_chunk_id(chunk),
            vector=np.asarray(vector, dtype="float32"),
            text=text,
            metadata=_chunk_metadata(chunk),
        ))
    return embedded
