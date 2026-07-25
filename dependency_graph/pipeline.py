"""
Dependency Graph Pipeline

Complete repository pipeline.

Repository
    ↓
GraphBuilder
    ↓
DependencyGraph
    ↓
Export JSON
"""

from pathlib import Path

from graph_builder import GraphBuilder
from exporter import GraphExporter
from models import DependencyGraph


class DependencyGraphPipeline:

    def __init__(
        self,
        repository_root: Path,
        output_dir: Path | None = None,
    ):

        self.repository_root = Path(repository_root)

        if output_dir is None:
            output_dir = self.repository_root / "graph_output"

        self.output_dir = Path(output_dir)

        self.builder = GraphBuilder(
            self.repository_root
        )

        self.exporter = GraphExporter(
            self.output_dir
        )

    # ------------------------------------------------------

    def run(
        self,
        export_json: bool = True,
        export_adjacency: bool = True,
    ) -> DependencyGraph:

        print("=" * 80)
        print("BUILDING DEPENDENCY GRAPH")
        print("=" * 80)

        graph = self.builder.build()

        print()

        print("=" * 80)
        print("GRAPH SUMMARY")
        print("=" * 80)

        print(f"Nodes : {len(graph.nodes)}")
        print(f"Edges : {len(graph.edges)}")

        print()

        if export_json:

            path = self.exporter.export_json(graph)

            print("Dependency graph exported to")

            print(path)

            print()

        if export_adjacency:

            path = self.exporter.export_adjacency(graph)

            print("Adjacency list exported to")

            print(path)

            print()

        return graph