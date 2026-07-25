"""
Shared data models for AST-aware chunking.

These dataclasses are used throughout the chunking pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class ChunkMetadata:
    """
    Metadata attached to every code chunk.
    """

    file_path: Path
    language: str

    symbol_name: str
    symbol_type: str  # function | class | method

    parent_class: Optional[str]

    start_line: int
    end_line: int

    start_byte: int
    end_byte: int

    token_count: int = 0


@dataclass(slots=True)
class CodeChunk:
    """
    Represents one semantic chunk of source code.
    """

    source_code: str
    metadata: ChunkMetadata

    @property
    def num_lines(self) -> int:
        return self.metadata.end_line - self.metadata.start_line + 1

    def __len__(self) -> int:
        return len(self.source_code)

    def __repr__(self) -> str:
        return (
            f"CodeChunk("
            f"{self.metadata.symbol_type}="
            f"{self.metadata.symbol_name}, "
            f"lines={self.metadata.start_line}-"
            f"{self.metadata.end_line})"
        )