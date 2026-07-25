"""
Graph data models.

Represents a lightweight dependency graph
for a source repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------


@dataclass(slots=True)
class GraphNode:
    """
    Represents a function, class or method.
    """

    id: str

    name: str

    symbol_type: str

    file_path: str

    language: str

    parent_class: Optional[str] = None


# ---------------------------------------------------------


@dataclass(slots=True)
class GraphEdge:
    """
    Relationship between two nodes.
    """

    source: str

    target: str

    relation: str


# ---------------------------------------------------------


@dataclass
class DependencyGraph:
    """
    Lightweight dependency graph.
    """

    nodes: Dict[str, GraphNode] = field(default_factory=dict)

    edges: List[GraphEdge] = field(default_factory=list)

    adjacency: Dict[str, List[str]] = field(default_factory=dict)

    # -----------------------------------------------------

    def add_node(self, node: GraphNode):

        if node.id not in self.nodes:

            self.nodes[node.id] = node

            self.adjacency[node.id] = []

    # -----------------------------------------------------

    def add_edge(
        self,
        source: str,
        target: str,
        relation: str = "calls",
    ):

        self.edges.append(

            GraphEdge(
                source=source,
                target=target,
                relation=relation,
            )
        )

        self.adjacency.setdefault(source, []).append(target)

    # -----------------------------------------------------

    def neighbors(
        self,
        node_id: str,
    ) -> List[str]:

        return self.adjacency.get(node_id, [])