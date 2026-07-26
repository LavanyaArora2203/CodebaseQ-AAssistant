"""
manager.py

High-level embedding manager for hybrid retrieval.

Pipeline:

Chunks
    ↓
Formatter
    ↓
Cache
    ↓
Dense + Sparse Embeddings
    ↓
Cache Update
    ↓
Return Embedded Chunks
"""

from __future__ import annotations

from typing import Any, Dict, List

from .cache import EmbeddingCache
from .embedders import get_embedder
from .formatter import ChunkFormatter


class EmbeddingManager:
    """
    High-level embedding pipeline.

    Responsible for:

    - Formatting chunks
    - Cache lookup
    - Batch embedding
    - Cache updates
    """

    def __init__(
        self,
        provider: str,
        batch_size: int = 32,
        cache_path: str = ".cache/embeddings.db",
        **provider_kwargs,
    ):

        self.batch_size = batch_size

        self.cache = EmbeddingCache(cache_path)

        self.embedder = get_embedder(
            provider,
            **provider_kwargs,
        )

    # ---------------------------------------------------------
    # Main API
    # ---------------------------------------------------------

    def embed_chunks(
        self,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Embed repository chunks.

        Returns
        -------

        [
            {
                "chunk": chunk,

                "dense": [...],

                "sparse": {
                    "indices": [...],
                    "values": [...]
                }
            }
        ]
        """

        formatted_texts = [
            ChunkFormatter.format(chunk)
            for chunk in chunks
        ]

        results = [None] * len(chunks)

        uncached_indices = []
        uncached_texts = []

        # ----------------------------------------
        # Cache lookup
        # ----------------------------------------

        for idx, text in enumerate(formatted_texts):

            cached = self.cache.get(text)

            if cached is not None:

                results[idx] = {
                    "chunk": chunks[idx],
                    "dense": cached["dense"],
                    "sparse": cached["sparse"],
                }

            else:

                uncached_indices.append(idx)
                uncached_texts.append(text)

        # ----------------------------------------
        # Batch embedding
        # ----------------------------------------

        for start in range(
            0,
            len(uncached_texts),
            self.batch_size,
        ):

            batch_texts = uncached_texts[
                start:start + self.batch_size
            ]

            batch_embeddings = self.embedder.embed(
                batch_texts
            )

            for text, embedding in zip(
                batch_texts,
                batch_embeddings,
            ):

                self.cache.set(
                    text,
                    embedding,
                )

        # ----------------------------------------
        # Read newly cached embeddings
        # ----------------------------------------

        for idx in uncached_indices:

            embedding = self.cache.get(
                formatted_texts[idx]
            )

            results[idx] = {
                "chunk": chunks[idx],
                "dense": embedding["dense"],
                "sparse": embedding["sparse"],
            }

        return results

    # ---------------------------------------------------------
    # Cache
    # ---------------------------------------------------------

    def clear_cache(self):

        self.cache.clear()

    def close(self):

        self.cache.close()

    def __enter__(self):

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):

        self.close()