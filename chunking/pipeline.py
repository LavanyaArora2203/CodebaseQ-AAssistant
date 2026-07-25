"""
AST-aware Chunking Pipeline

Pipeline:
Repository
    ↓
Filtered Files
    ↓
Language Detection
    ↓
Tree-sitter Parsing
    ↓
AST Extraction
    ↓
Chunk Merging
    ↓
Metadata Enrichment
"""

from pathlib import Path

from ingestion.file_filtering import FileFilter
from ingestion.language_detection import LanguageDetector

from parser import ASTParser
from chunk_extractor import ChunkExtractor
from chunk_merger import ChunkMerger
from metadata import MetadataBuilder


class ChunkingPipeline:

    def __init__(
        self,
        repository_root: Path,
        repository_name: str,
        max_tokens: int = 300,
    ):

        self.repository_root = repository_root
        self.repository_name = repository_name

        self.file_filter = FileFilter(repository_root)
        self.language_detector = LanguageDetector()

        self.parser = ASTParser()
        self.extractor = ChunkExtractor()
        self.merger = ChunkMerger(max_tokens=max_tokens)

        self.metadata_builder = MetadataBuilder(
            repository_name=repository_name,
            repository_root=repository_root,
        )

    # ---------------------------------------------------------

    def run(self):

        final_chunks = []

        files = list(self.file_filter.get_indexable_files())

        print(f"\nFound {len(files)} candidate files.\n")

        for file in files:

            language = self.language_detector.detect(file)

            if language is None:
                continue

            if not language.tree_sitter_supported:
                continue

            try:

                tree, source = self.parser.parse_file(
                    file,
                    language.language,
                )

                chunks = self.extractor.extract(
                    tree.root_node,
                    source,
                    file,
                    language.language,
                )

                chunks = self.merger.merge(chunks)

                for chunk in chunks:

                    metadata = self.metadata_builder.enrich(chunk)

                    final_chunks.append(
                        {
                            "chunk": chunk,
                            "metadata": metadata,
                        }
                    )

            except Exception as e:

                print(f"Skipping {file}")

                print(e)

        return final_chunks