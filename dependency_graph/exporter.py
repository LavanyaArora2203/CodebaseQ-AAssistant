"""
Dependency Graph Exporter

Supports exporting the dependency graph into
different formats.

Currently:
    ✓ JSON

Future:
    - Neo4j Cypher
    - GraphML
    - NetworkX
"""

from __future__ import annotations

import json
from pathlib import Path

from models import DependencyGraph


class GraphExporter:

    def __init__(self, output_dir: Path):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ---------------------------------------------------------

    def export_json(
        self,
        graph: DependencyGraph,
        filename: str = "dependency_graph.json",
    ) -> Path:
        """
        Export graph as JSON.

        Returns
        -------
        Path
            Path to generated JSON file.
        """

        output = {

            "nodes": [

                {
                    "id": node.id,
                    "name": node.name,
                    "symbol_type": node.symbol_type,
                    "file_path": node.file_path,
                    "language": node.language,
                    "parent_class": node.parent_class,
                }

                for node in graph.nodes.values()

            ],

            "edges": [

                {
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation,
                }

                for edge in graph.edges

            ],

            "adjacency": graph.adjacency,
        }

        output_path = self.output_dir / filename

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                output,
                f,
                indent=4,
                ensure_ascii=False,
            )

        return output_path

    # ---------------------------------------------------------

    def export_adjacency(
        self,
        graph: DependencyGraph,
        filename: str = "adjacency.json",
    ) -> Path:
        """
        Export only adjacency list.
        """

        output_path = self.output_dir / filename

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                graph.adjacency,
                f,
                indent=4,
                ensure_ascii=False,
            )

        return output_path