"""
cache.py

Persistent SQLite cache for hybrid embeddings.

Each cache entry stores:
- Dense embedding
- Sparse embedding

The cache key is the SHA256 hash of the formatted chunk text.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional


class EmbeddingCache:
    """SQLite-backed cache for hybrid embeddings."""

    def __init__(
        self,
        cache_path: str = ".cache/embeddings.db",
    ) -> None:

        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.conn = sqlite3.connect(self.cache_path)
        self._create_table()

    def _create_table(self) -> None:

        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (

                hash TEXT PRIMARY KEY,

                embedding TEXT NOT NULL

            )
            """
        )

        self.conn.commit()

    @staticmethod
    def compute_hash(text: str) -> str:
        """Compute SHA256 hash."""

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

    def get(
        self,
        text: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached hybrid embedding.

        Returns

        {
            "dense": [...],
            "sparse": {
                "indices": [...],
                "values": [...]
            }
        }
        """

        chunk_hash = self.compute_hash(text)

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT embedding
            FROM embeddings
            WHERE hash = ?
            """,
            (chunk_hash,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return json.loads(row[0])

    def set(
        self,
        text: str,
        embedding: Dict[str, Any],
    ) -> None:
        """
        Store hybrid embedding.
        """

        chunk_hash = self.compute_hash(text)

        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO embeddings
            VALUES (?, ?)
            """,
            (
                chunk_hash,
                json.dumps(embedding),
            ),
        )

        self.conn.commit()

    def contains(
        self,
        text: str,
    ) -> bool:

        chunk_hash = self.compute_hash(text)

        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM embeddings
            WHERE hash = ?
            """,
            (chunk_hash,),
        )

        return cursor.fetchone() is not None

    def clear(self) -> None:
        """Delete all cached embeddings."""

        cursor = self.conn.cursor()

        cursor.execute(
            "DELETE FROM embeddings"
        )

        self.conn.commit()

    def close(self) -> None:
        """Close SQLite connection."""

        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()