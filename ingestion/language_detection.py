"""
Language Detection Module

Responsibilities
----------------
- Detect programming language from file extension
- Handle special filenames (Dockerfile, Makefile, etc.)
- Report Tree-sitter grammar availability
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# -------------------------------------------------------
# Extension -> Language Mapping
# -------------------------------------------------------

EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "c_sharp",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".md": "markdown",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".toml": "toml",
    ".ini": "ini",
}


# -------------------------------------------------------
# Special filenames
# -------------------------------------------------------

SPECIAL_FILENAMES = {
    "Dockerfile": "dockerfile",
    "Makefile": "make",
    "CMakeLists.txt": "cmake",
    ".gitignore": "gitignore",
    ".dockerignore": "dockerignore",
    ".env": "dotenv",
}


# -------------------------------------------------------
# Languages supported by Tree-sitter
# (expand this as you install grammars)
# -------------------------------------------------------

TREE_SITTER_SUPPORTED = {
    "python",
    "javascript",
    "typescript",
    "tsx",
    "java",
    "go",
    "rust",
    "cpp",
    "c",
    "c_sharp",
    "php",
    "ruby",
    "html",
    "css",
    "json",
    "yaml",
    "bash",
    "markdown",
}


# -------------------------------------------------------

@dataclass(slots=True)
class LanguageInfo:
    """
    Information about a detected language.
    """

    language: str
    extension: str
    tree_sitter_supported: bool


# -------------------------------------------------------

class LanguageDetector:
    """
    Detect programming language of a source file.
    """

    def detect(self, file_path: Path) -> Optional[LanguageInfo]:

        # Check special filenames first
        if file_path.name in SPECIAL_FILENAMES:

            language = SPECIAL_FILENAMES[file_path.name]

            return LanguageInfo(
                language=language,
                extension=file_path.name,
                tree_sitter_supported=language in TREE_SITTER_SUPPORTED,
            )

        # Extension lookup
        ext = file_path.suffix.lower()

        language = EXTENSION_MAP.get(ext)

        if language is None:
            return None

        return LanguageInfo(
            language=language,
            extension=ext,
            tree_sitter_supported=language in TREE_SITTER_SUPPORTED,
        )

    # ---------------------------------------------------

    def supports_tree_sitter(self, language: str) -> bool:
        """
        Check whether a Tree-sitter grammar is available.
        """

        return language in TREE_SITTER_SUPPORTED


# -------------------------------------------------------
# Example
# -------------------------------------------------------

if __name__ == "__main__":

    detector = LanguageDetector()

    examples = [
        Path("main.py"),
        Path("App.tsx"),
        Path("Dockerfile"),
        Path("README.md"),
        Path("Cargo.toml"),
        Path("unknown.xyz"),
    ]

    for file in examples:

        info = detector.detect(file)

        print(file)

        if info:
            print(info)
        else:
            print("Unknown language")

        print("-" * 40)