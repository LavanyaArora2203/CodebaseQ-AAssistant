#!/usr/bin/env python3
"""
vector_store.py

A local vector database: FAISS for the vector index + a JSON sidecar for
metadata, chosen over Chroma/Qdrant specifically because it needs nothing
running (no server process, no model download at query time) and installs
as a pure pip package — the most reliable option in network-restricted
environments. If you want a swap-in alternative:

    Chroma:  `chromadb.PersistentClient(path=...)`, a `.get_or_create_collection()`,
             then `.add(ids=..., embeddings=..., metadatas=..., documents=...)`
             and `.query(query_embeddings=..., n_results=...)`. Very similar
             API shape to VectorStore below, runs embedded (no server) too.
    Qdrant:  `qdrant_client.QdrantClient(path=...)` for local embedded mode,
             or point at a running Qdrant server for production. Supports
             richer server-side metadata filtering than FAISS out of the box.

This module stores vectors in a FAISS `IndexFlatIP` (inner product — since
embeddings are L2-normalized upstream, inner product == cosine similarity)
plus a parallel Python list of metadata dicts, persisted as:

    <path>.faiss   — the FAISS index
    <path>.meta.json — {"ids": [...], "texts": [...], "metadatas": [...]}

Both files are written together by save(); load() requires both to exist.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, List, Optional

import faiss
import numpy as np

from embeddings import EmbeddedChunk


class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.ids: List[str] = []
        self.texts: List[str] = []
        self.metadatas: List[dict] = []
        self._id_to_pos = {}  # id -> row index in self.index, for dedup/update

    # ---- insert -------------------------------------------------------------

    def insert(self, embedded_chunks: List[EmbeddedChunk]) -> int:
        """
        Insert embedded chunks. Chunks whose id already exists are skipped
        (call delete_by_id first if you want to overwrite). Returns the
        number of vectors actually inserted.
        """
        new_vectors = []
        inserted = 0
        for ec in embedded_chunks:
            if ec.id in self._id_to_pos:
                continue
            if ec.vector.shape[0] != self.dim:
                raise ValueError(
                    f"Embedding dim mismatch: store dim={self.dim}, "
                    f"chunk '{ec.id}' vector dim={ec.vector.shape[0]}"
                )
            self._id_to_pos[ec.id] = len(self.ids)
            self.ids.append(ec.id)
            self.texts.append(ec.text)
            self.metadatas.append(ec.metadata)
            new_vectors.append(ec.vector)
            inserted += 1

        if new_vectors:
            self.index.add(np.stack(new_vectors).astype("float32"))
        return inserted

    def delete_by_id(self, chunk_id: str) -> bool:
        """
        FAISS's flat index doesn't support in-place row deletion cheaply,
        so this rebuilds the index without the given id. Fine for periodic
        re-indexing; avoid calling this in a tight loop over many deletes.
        """
        if chunk_id not in self._id_to_pos:
            return False
        keep = [i for i in range(len(self.ids)) if self.ids[i] != chunk_id]
        all_vectors = np.stack([self.index.reconstruct(i) for i in range(len(self.ids))])
        kept_vectors = all_vectors[keep]

        self.ids = [self.ids[i] for i in keep]
        self.texts = [self.texts[i] for i in keep]
        self.metadatas = [self.metadatas[i] for i in keep]
        self._id_to_pos = {cid: pos for pos, cid in enumerate(self.ids)}

        self.index = faiss.IndexFlatIP(self.dim)
        if len(kept_vectors):
            self.index.add(kept_vectors.astype("float32"))
        return True

    # ---- query ----------------------------------------------------------------

    def query(self, query_vector: np.ndarray, top_k: int = 5,
              where: Optional[Callable[[dict], bool]] = None) -> List[dict]:
        """
        Return the top_k most similar chunks to query_vector.

        `where` is an optional predicate over a metadata dict, e.g.:
            where=lambda m: m["chunk_type"] == "function"
            where=lambda m: m["language"] == "python" and m["parent_class"] == "Widget"

        Filtering is applied post-search over an oversampled candidate pool
        (since FAISS's flat index has no native metadata filter); if very
        few results match a narrow filter, increase `top_k` or the internal
        oversampling factor below.

        Returns a list of dicts: {id, score, text, metadata}, best first.
        """
        if self.index.ntotal == 0:
            return []

        query_vector = np.asarray(query_vector, dtype="float32").reshape(1, -1)
        search_k = top_k if where is None else min(self.index.ntotal, max(top_k * 10, 50))

        scores, indices = self.index.search(query_vector, search_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            metadata = self.metadatas[idx]
            if where is not None and not where(metadata):
                continue
            results.append({
                "id": self.ids[idx],
                "score": float(score),
                "text": self.texts[idx],
                "metadata": metadata,
            })
            if len(results) >= top_k:
                break
        return results

    # ---- persistence ------------------------------------------------------

    def save(self, path: str | Path) -> None:
        path = Path(path)
        faiss.write_index(self.index, str(path.with_suffix(".faiss")))
        meta_path = path.with_suffix(".meta.json")
        meta_path.write_text(json.dumps({
            "dim": self.dim,
            "ids": self.ids,
            "texts": self.texts,
            "metadatas": self.metadatas,
        }))

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        path = Path(path)
        meta_path = path.with_suffix(".meta.json")
        index_path = path.with_suffix(".faiss")
        if not meta_path.exists() or not index_path.exists():
            raise FileNotFoundError(f"Missing index files for '{path}' (.faiss / .meta.json)")

        meta = json.loads(meta_path.read_text())
        store = cls(dim=meta["dim"])
        store.index = faiss.read_index(str(index_path))
        store.ids = meta["ids"]
        store.texts = meta["texts"]
        store.metadatas = meta["metadatas"]
        store._id_to_pos = {cid: pos for pos, cid in enumerate(store.ids)}
        return store

    def __len__(self) -> int:
        return len(self.ids)
