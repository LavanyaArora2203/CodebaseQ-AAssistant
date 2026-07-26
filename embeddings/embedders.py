"""
embedders.py

Hybrid embedding providers for the GitHub Repository RAG pipeline.

Supports:

• Dense embeddings
    - Voyage Code-3
    - Qwen3 Embedding

• Sparse embeddings
    - FastEmbed SPLADE/BM25

All providers return the same output format.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


# ---------------------------------------------------------
# Base Class
# ---------------------------------------------------------


class BaseEmbedder(ABC):
    """Base class for all hybrid embedders."""

    @abstractmethod
    def embed(
        self,
        texts: List[str],
    ) -> List[Dict]:
        """
        Returns

        [
            {
                "dense": [...],
                "sparse": {
                    "indices": [...],
                    "values": [...]
                }
            }
        ]
        """
        raise NotImplementedError


# ---------------------------------------------------------
# Sparse Encoder
# ---------------------------------------------------------


class SparseEmbedder:
    """
    FastEmbed sparse encoder.

    Uses SPLADE/BM25 sparse embeddings compatible with Qdrant.
    """

    def __init__(
        self,
        model_name: str = "Qdrant/bm25",
    ):

        try:
            from fastembed import SparseTextEmbedding
        except ImportError:
            raise ImportError(
                "Install FastEmbed:\n\n"
                "pip install fastembed"
            )

        self.model = SparseTextEmbedding(model_name=model_name)

    def embed(
        self,
        texts: List[str],
    ) -> List[Dict]:

        vectors = []

        embeddings = list(
            self.model.embed(texts)
        )

        for embedding in embeddings:

            vectors.append(
                {
                    "indices": embedding.indices.tolist(),
                    "values": embedding.values.tolist(),
                }
            )

        return vectors


# ---------------------------------------------------------
# Voyage
# ---------------------------------------------------------


class VoyageEmbedder(BaseEmbedder):

    def __init__(
        self,
        api_key: str,
        model: str = "voyage-code-3",
        sparse_model: str = "Qdrant/bm25",
    ):

        try:
            import voyageai
        except ImportError:
            raise ImportError(
                "pip install voyageai"
            )

        self.client = voyageai.Client(
            api_key=api_key
        )

        self.model = model

        self.sparse = SparseEmbedder(
            sparse_model
        )

    def embed(
        self,
        texts: List[str],
    ) -> List[Dict]:

        dense = self.client.embed(
            texts=texts,
            model=self.model,
        ).embeddings

        sparse = self.sparse.embed(
            texts
        )

        results = []

        for d, s in zip(dense, sparse):

            results.append(
                {
                    "dense": d,
                    "sparse": s,
                }
            )

        return results


# ---------------------------------------------------------
# Qwen
# ---------------------------------------------------------


class QwenEmbedder(BaseEmbedder):

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-0.6B",
        device: Optional[str] = None,
        sparse_model: str = "Qdrant/bm25",
    ):

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "pip install sentence-transformers"
            )

        self.model = SentenceTransformer(
            model_name,
            device=device,
            trust_remote_code=True,
        )

        self.sparse = SparseEmbedder(
            sparse_model
        )

    def embed(
        self,
        texts: List[str],
    ) -> List[Dict]:

        dense = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        sparse = self.sparse.embed(
            texts
        )

        results = []

        for d, s in zip(dense, sparse):

            results.append(
                {
                    "dense": d,
                    "sparse": s,
                }
            )

        return results


# ---------------------------------------------------------
# Factory
# ---------------------------------------------------------


def get_embedder(
    provider: str,
    **kwargs,
) -> BaseEmbedder:

    provider = provider.lower()

    if provider == "voyage":
        return VoyageEmbedder(**kwargs)

    if provider == "qwen":
        return QwenEmbedder(**kwargs)

    raise ValueError(
        f"Unsupported provider: {provider}"
    )