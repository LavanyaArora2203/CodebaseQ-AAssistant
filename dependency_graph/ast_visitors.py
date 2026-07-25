"""
Python AST Visitor using Tree-sitter.

Extracts:
- Function definitions
- Class definitions
- Method definitions
- Function calls
- Imports

Builds a lightweight dependency graph.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from tree_sitter import Node

from models import DependencyGraph, GraphNode


class PythonASTVisitor:

    def __init__(
        self,
        graph: DependencyGraph,
        file_path: Path,
    ):
        self.graph = graph
        self.file_path = str(file_path)

        self.current_symbol: Optional[str] = None
        self.current_class: Optional[str] = None

    # ---------------------------------------------------------

    def visit(
        self,
        node: Node,
    ):

        handler = getattr(
            self,
            f"_visit_{node.type}",
            self._generic_visit,
        )

        handler(node)

    # ---------------------------------------------------------

    def _generic_visit(
        self,
        node: Node,
    ):

        for child in node.children:
            self.visit(child)

    # ---------------------------------------------------------
    # CLASS
    # ---------------------------------------------------------

    def _visit_class_definition(
        self,
        node: Node,
    ):

        class_name = self._identifier(node)

        self.graph.add_node(

            GraphNode(
                id=class_name,
                name=class_name,
                symbol_type="class",
                file_path=self.file_path,
                language="python",
            )
        )

        previous_class = self.current_class
        previous_symbol = self.current_symbol

        self.current_class = class_name
        self.current_symbol = class_name

        for child in node.children:
            self.visit(child)

        self.current_class = previous_class
        self.current_symbol = previous_symbol

    # ---------------------------------------------------------
    # FUNCTION
    # ---------------------------------------------------------

    def _visit_function_definition(
        self,
        node: Node,
    ):

        function_name = self._identifier(node)

        symbol_type = (
            "method"
            if self.current_class
            else "function"
        )

        node_id = (
            f"{self.current_class}.{function_name}"
            if self.current_class
            else function_name
        )

        self.graph.add_node(

            GraphNode(
                id=node_id,
                name=function_name,
                symbol_type=symbol_type,
                file_path=self.file_path,
                language="python",
                parent_class=self.current_class,
            )
        )

        previous_symbol = self.current_symbol

        self.current_symbol = node_id

        for child in node.children:
            self.visit(child)

        self.current_symbol = previous_symbol

    # ---------------------------------------------------------
    # CALLS
    # ---------------------------------------------------------

    def _visit_call(
        self,
        node: Node,
    ):

        if self.current_symbol is None:
            return

        function = node.child_by_field_name("function")

        if function is None:
            return

        target = function.text.decode()

        self.graph.add_edge(
            self.current_symbol,
            target,
            "calls",
        )

        self._generic_visit(node)

    # ---------------------------------------------------------
    # IMPORTS
    # ---------------------------------------------------------

    def _visit_import_statement(
        self,
        node: Node,
    ):

        if self.current_symbol is None:
            return

        for child in node.children:

            if child.type == "dotted_name":

                self.graph.add_edge(
                    self.current_symbol,
                    child.text.decode(),
                    "imports",
                )

    # ---------------------------------------------------------

    def _visit_import_from_statement(
        self,
        node: Node,
    ):

        if self.current_symbol is None:
            return

        module = None

        for child in node.children:

            if child.type == "dotted_name":

                module = child.text.decode()

                break

        if module:

            self.graph.add_edge(
                self.current_symbol,
                module,
                "imports",
            )

    # ---------------------------------------------------------

    def _identifier(
        self,
        node: Node,
    ) -> str:

        for child in node.children:

            if child.type == "identifier":

                return child.text.decode()

        return "<anonymous>"