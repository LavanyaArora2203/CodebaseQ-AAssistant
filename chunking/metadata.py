"""
Metadata Builder

Enriches extracted chunks with repository-level metadata.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from models import CodeChunk


class MetadataBuilder:

    def __init__(
        self,
        repository_name: str,
        repository_root: Path,
    ):
        self.repository_name = repository_name
        self.repository_root = repository_root

    # --------------------------------------------------------

    def enrich(
        self,
        chunk: CodeChunk,
    ) -> dict:
        """
        Convert a CodeChunk into a metadata dictionary
        suitable for vector databases.
        """

        relative_path = chunk.metadata.file_path.relative_to(
            self.repository_root
        )

        return {

            "chunk_id": self.chunk_id(chunk),

            "repository": self.repository_name,

            "file_path": str(relative_path),

            "absolute_path": str(chunk.metadata.file_path),

            "language": chunk.metadata.language,

            "symbol_name": chunk.metadata.symbol_name,

            "symbol_type": chunk.metadata.symbol_type,

            "parent_class": chunk.metadata.parent_class,

            "start_line": chunk.metadata.start_line,

            "end_line": chunk.metadata.end_line,

            "start_byte": chunk.metadata.start_byte,

            "end_byte": chunk.metadata.end_byte,

            "token_count": chunk.metadata.token_count,

            "num_lines": chunk.num_lines,

            "file_extension": chunk.metadata.file_path.suffix,

            "sha256": hashlib.sha256(
                chunk.source_code.encode("utf8")
            ).hexdigest(),
        }

    # --------------------------------------------------------

    def chunk_id(
        self,
        chunk: CodeChunk,
    ) -> str:
        """
        Generate a stable unique identifier.
        """

        key = (
            f"{chunk.metadata.file_path}:"
            f"{chunk.metadata.symbol_name}:"
            f"{chunk.metadata.start_line}:"
            f"{chunk.metadata.end_line}"
        )

        return hashlib.sha256(
            key.encode("utf8")
        ).hexdigest()