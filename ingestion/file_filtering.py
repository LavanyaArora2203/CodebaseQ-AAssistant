"""
File Filtering Module

Responsibilities
----------------
- Respect .gitignore
- Skip hidden/system directories
- Skip binaries
- Skip lockfiles
- Skip generated/minified code
- Return only source files suitable for indexing.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Iterable

import pathspec

# ---------------------------------------------------
# Directories that should never be indexed
# ---------------------------------------------------

SKIP_DIRECTORIES = {
    ".git",
    ".github",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "target",
    ".next",
    ".idea",
    ".vscode",
    "coverage",
}


# ---------------------------------------------------
# Lock files
# ---------------------------------------------------

LOCKFILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "Pipfile.lock",
    "Gemfile.lock",
    "composer.lock",
}


# ---------------------------------------------------
# Binary extensions
# ---------------------------------------------------

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".7z",
    ".rar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".class",
    ".jar",
    ".pyc",
    ".o",
    ".a",
    ".bin",
}


# ---------------------------------------------------
# Generated files
# ---------------------------------------------------

GENERATED_PATTERNS = (
    ".min.js",
    ".bundle.js",
    ".generated.",
    ".gen.",
)


class FileFilter:
    """
    Filters repository files before indexing.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.gitignore = self._load_gitignore()

    # ------------------------------------------------

    def _load_gitignore(self):
        gitignore = self.repo_root / ".gitignore"

        if not gitignore.exists():
            return None

        with gitignore.open() as f:
            return pathspec.PathSpec.from_lines(
                "gitwildmatch",
                f.readlines(),
            )

    # ------------------------------------------------

    def is_gitignored(self, path: Path) -> bool:

        if self.gitignore is None:
            return False

        relative = path.relative_to(self.repo_root)

        return self.gitignore.match_file(str(relative))

    # ------------------------------------------------

    def is_binary(self, path: Path) -> bool:

        if path.suffix.lower() in BINARY_EXTENSIONS:
            return True

        mime, _ = mimetypes.guess_type(path)

        if mime and not mime.startswith("text"):
            return True

        try:
            with open(path, "rb") as f:
                chunk = f.read(2048)

            return b"\x00" in chunk

        except Exception:
            return True

    # ------------------------------------------------

    def is_generated(self, path: Path) -> bool:

        name = path.name.lower()

        for pattern in GENERATED_PATTERNS:
            if pattern in name:
                return True

        try:
            with open(path, encoding="utf8", errors="ignore") as f:
                first_lines = "".join(f.readline() for _ in range(5)).lower()

            generated_headers = (
                "auto-generated",
                "automatically generated",
                "do not edit",
                "@generated",
            )

            return any(h in first_lines for h in generated_headers)

        except Exception:
            return False

    # ------------------------------------------------

    def should_index(self, path: Path) -> bool:

        # directories
        if any(part in SKIP_DIRECTORIES for part in path.parts):
            return False

        # .gitignore
        if self.is_gitignored(path):
            return False

        # lockfiles
        if path.name in LOCKFILES:
            return False

        # binary
        if self.is_binary(path):
            return False

        # generated
        if self.is_generated(path):
            return False

        return True

    # ------------------------------------------------

    def get_indexable_files(self) -> Iterable[Path]:
        """
        Walk the repository and return all indexable files.
        """

        for file in self.repo_root.rglob("*"):

            if not file.is_file():
                continue

            if self.should_index(file):
                yield file


# ---------------------------------------------------
# Example
# ---------------------------------------------------

if __name__ == "__main__":

    repo = Path("/path/to/cloned/repository")

    ff = FileFilter(repo)

    files = list(ff.get_indexable_files())

    print(f"Indexable files: {len(files)}")

    for f in files[:20]:
        print(f)