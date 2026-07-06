"""
metadata_extractor.py

Extracts metadata for AST chunks before embedding.

Compatible with:
- Tree-sitter AST Chunking
- LangChain Documents
- Chroma
- FAISS
- Pinecone
"""

from pathlib import Path
from datetime import datetime
import subprocess
from typing import Dict, Optional


class MetadataExtractor:
    """
    Extract metadata for every chunk.
    """

    def __init__(self, root_directory: Optional[str] = None):
        self.root_directory = (
            Path(root_directory).resolve()
            if root_directory
            else None
        )

    ###########################################################
    # Public API
    ###########################################################

    def extract(
        self,
        file_path: str,
        chunk_type: str,
        start_line: int,
        end_line: int,
        function_name=None,
        class_name=None,
        parent_class=None,
        language="python"
    ) -> Dict:
        """
        Returns metadata dictionary.
        """

        path = Path(file_path)

        metadata = {

    "file_path": str(path),

    "language": language,

    "chunk_type": chunk_type,

    "function_name": function_name,

    "class_name": class_name,

    "parent_class": parent_class,

    "start_line": start_line,

    "end_line": end_line
}

        metadata.update(self._git_metadata(file_path, start_line))

        return metadata

    ###########################################################
    # Internal helpers
    ###########################################################

    def _module_name(self, path: Path) -> str:
        """
        Convert file path into module name.

        src/utils/math.py

        -->

        src.utils.math
        """

        if self.root_directory:

            try:
                relative = path.resolve().relative_to(
                    self.root_directory
                )

            except Exception:
                relative = path

        else:
            relative = path

        return ".".join(relative.with_suffix("").parts)

    ###########################################################

    def _git_metadata(
        self,
        file_path: str,
        line: int
    ) -> Dict:

        metadata = {
            "git_author": None,
            "git_commit": None,
            "git_date": None
        }

        try:

            blame = subprocess.check_output(
                [
                    "git",
                    "blame",
                    "-L",
                    f"{line},{line}",
                    "--line-porcelain",
                    file_path
                ],
                stderr=subprocess.DEVNULL,
                text=True
            )

            commit = None
            author = None
            timestamp = None

            for row in blame.splitlines():

                if row.startswith("author "):
                    author = row.replace("author ", "")

                elif row.startswith("author-time "):
                    timestamp = int(
                        row.replace("author-time ", "")
                    )

                elif (
                    len(row.split()) > 0
                    and len(row.split()[0]) == 40
                ):
                    commit = row.split()[0]

            metadata["git_author"] = author
            metadata["git_commit"] = commit

            if timestamp:

                metadata["git_date"] = (
                    datetime.utcfromtimestamp(
                        timestamp
                    ).isoformat()
                )

        except Exception:
            pass

        return metadata