"""
Tree-sitter Parser Module

Responsibilities
----------------
- Read source files
- Parse source code using Tree-sitter
- Return the AST (Tree object)

NOTE:
This module DOES NOT extract functions/classes.
It only produces the AST.
"""

from __future__ import annotations

from pathlib import Path
from tree_sitter import Tree

from language_registry import LanguageRegistry


class ASTParser:
    """
    Parses source files into Tree-sitter ASTs.
    """

    def __init__(self):
        self.registry = LanguageRegistry()

    def parse_file(
        self,
        file_path: Path,
        language: str,
    ) -> tuple[Tree, bytes]:
        """
        Parse a source file.

        Parameters
        ----------
        file_path : Path
            Path to source file.

        language : str
            Programming language.

        Returns
        -------
        (Tree, bytes)

        Tree:
            Tree-sitter AST

        bytes:
            Original source code as bytes.
            Required because Tree-sitter nodes store byte offsets.
        """

        parser = self.registry.get_parser(language)

        source = file_path.read_bytes()

        tree = parser.parse(source)

        return tree, source

    def parse_source(
        self,
        source: str,
        language: str,
    ) -> tuple[Tree, bytes]:
        """
        Parse source code directly from a string.
        Useful for testing.
        """

        parser = self.registry.get_parser(language)

        source_bytes = source.encode("utf-8")

        tree = parser.parse(source_bytes)

        return tree, source_bytes