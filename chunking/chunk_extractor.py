"""
AST Chunk Extractor

Extracts semantic chunks from a Tree-sitter AST.

Current support:
- Python

Can easily be extended for:
- Java
- JavaScript
- TypeScript
- Go
- Rust
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from tree_sitter import Node

from models import ChunkMetadata, CodeChunk


class ChunkExtractor:

    def __init__(self):
        pass

    # ----------------------------------------------------

    def extract(
        self,
        root: Node,
        source: bytes,
        file_path: Path,
        language: str,
    ) -> List[CodeChunk]:

        if language != "python":
            raise NotImplementedError(
                f"{language} extractor not implemented."
            )

        chunks: List[CodeChunk] = []

        self._visit(
            node=root,
            source=source,
            file_path=file_path,
            language=language,
            chunks=chunks,
            parent_class=None,
        )

        return chunks

    # ----------------------------------------------------

    def _visit(
        self,
        node: Node,
        source: bytes,
        file_path: Path,
        language: str,
        chunks: List[CodeChunk],
        parent_class: Optional[str],
    ):

        if node.type == "class_definition":

            class_name = self._identifier(node)

            chunks.append(
                self._make_chunk(
                    node=node,
                    source=source,
                    file_path=file_path,
                    language=language,
                    symbol_name=class_name,
                    symbol_type="class",
                    parent_class=None,
                )
            )

            for child in node.children:
                self._visit(
                    child,
                    source,
                    file_path,
                    language,
                    chunks,
                    parent_class=class_name,
                )

            return

        if node.type == "function_definition":

            symbol_type = (
                "method"
                if parent_class
                else "function"
            )

            chunks.append(
                self._make_chunk(
                    node=node,
                    source=source,
                    file_path=file_path,
                    language=language,
                    symbol_name=self._identifier(node),
                    symbol_type=symbol_type,
                    parent_class=parent_class,
                )
            )

        for child in node.children:
            self._visit(
                child,
                source,
                file_path,
                language,
                chunks,
                parent_class,
            )

    # ----------------------------------------------------

    def _identifier(self, node: Node) -> str:

        for child in node.children:

            if child.type == "identifier":
                return child.text.decode()

        return "<anonymous>"

    # ----------------------------------------------------

    def _make_chunk(
        self,
        node: Node,
        source: bytes,
        file_path: Path,
        language: str,
        symbol_name: str,
        symbol_type: str,
        parent_class: Optional[str],
    ) -> CodeChunk:

        code = source[
            node.start_byte:node.end_byte
        ].decode(
            "utf8",
            errors="ignore",
        )

        metadata = ChunkMetadata(
            file_path=file_path,
            language=language,

            symbol_name=symbol_name,
            symbol_type=symbol_type,

            parent_class=parent_class,

            start_line=node.start_point.row + 1,
            end_line=node.end_point.row + 1,

            start_byte=node.start_byte,
            end_byte=node.end_byte,
        )

        return CodeChunk(
            source_code=code,
            metadata=metadata,
        )