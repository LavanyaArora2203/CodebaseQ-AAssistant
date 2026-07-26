"""
formatter.py

Formats code and documentation chunks into rich text suitable for
embedding models.

The goal is to provide enough semantic context (file path, symbol,
signature, etc.) to improve retrieval quality without modifying the
original chunk metadata.
"""

from __future__ import annotations

from typing import Any, Dict


class ChunkFormatter:
    """Formats repository chunks for embedding."""

    @staticmethod
    def format(chunk: Dict[str, Any]) -> str:
        """
        Format a chunk into embedding-ready text.

        Parameters
        ----------
        chunk : dict
            Repository chunk.

        Returns
        -------
        str
            Formatted text for embedding.
        """

        chunk_type = chunk.get("type", "").lower()

        if chunk_type == "documentation":
            return ChunkFormatter._format_documentation(chunk)

        return ChunkFormatter._format_code(chunk)

    @staticmethod
    def _format_code(chunk: Dict[str, Any]) -> str:
        """Format an AST/code chunk."""

        sections = []

        if chunk.get("path"):
            sections.append(f"Path:\n{chunk['path']}")

        if chunk.get("language"):
            sections.append(f"Language:\n{chunk['language']}")

        if chunk.get("type"):
            sections.append(f"Chunk Type:\n{chunk['type']}")

        if chunk.get("symbol"):
            sections.append(f"Symbol:\n{chunk['symbol']}")

        if chunk.get("signature"):
            sections.append(f"Signature:\n{chunk['signature']}")

        if chunk.get("docstring"):
            sections.append(f"Docstring:\n{chunk['docstring']}")

        if chunk.get("imports"):
            imports = ", ".join(chunk["imports"])
            sections.append(f"Imports:\n{imports}")

        if chunk.get("code"):
            sections.append(f"Code:\n{chunk['code']}")

        return "\n\n".join(sections)

    @staticmethod
    def _format_documentation(chunk: Dict[str, Any]) -> str:
        """Format a documentation chunk."""

        sections = []

        if chunk.get("path"):
            sections.append(f"Path:\n{chunk['path']}")

        sections.append("Chunk Type:\nDocumentation")

        if chunk.get("title"):
            sections.append(f"Title:\n{chunk['title']}")

        if chunk.get("content"):
            sections.append(f"Content:\n{chunk['content']}")

        return "\n\n".join(sections)