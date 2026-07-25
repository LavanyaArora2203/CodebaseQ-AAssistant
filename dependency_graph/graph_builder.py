"""
Repository Dependency Graph Builder

Coordinates:
    Repository
        ↓
    File Filtering
        ↓
    Language Detection
        ↓
    Tree-sitter Parsing
        ↓
    AST Visitor
        ↓
    Repository Dependency Graph
"""

from __future__ import annotations

from pathlib import Path

from ingestion.file_filtering import FileFilter
from ingestion.language_detection import LanguageDetector

from chunking.parser import ASTParser

from models import DependencyGraph
from ast_visitors import PythonASTVisitor


class GraphBuilder:

    def __init__(self, repository_root: Path):

        self.repository_root = Path(repository_root)

        self.file_filter = FileFilter(self.repository_root)

        self.language_detector = LanguageDetector()

        self.parser = ASTParser()

    # ---------------------------------------------------------

    def build(self) -> DependencyGraph:
        """
        Build dependency graph for the repository.
        """

        graph = DependencyGraph()

        files = list(
            self.file_filter.get_indexable_files()
        )

        print(f"\nScanning {len(files)} files...\n")

        for file_path in files:

            language_info = self.language_detector.detect(file_path)

            if language_info is None:
                continue

            if not language_info.tree_sitter_supported:
                continue

            language = language_info.language.lower()

            try:

                tree, _ = self.parser.parse_file(
                    file_path,
                    language,
                )

                # Currently only Python
                if language == "python":

                    visitor = PythonASTVisitor(
                        graph=graph,
                        file_path=file_path,
                    )

                    visitor.visit(tree.root_node)

            except Exception as e:

                print(f"Skipping {file_path}")

                print(e)

        return graph