#!/usr/bin/env python3
"""
tag_repo_files.py

Recursively walk a GitHub repo (or any directory) and tag each file by type:
- source: .py / .js / .go
- docs: README* or .md
- config: .yaml / .yml / .json / .toml
- test: filenames/paths matching common test conventions
- other: anything else

Usage:
    python tag_repo_files.py /path/to/repo
    python tag_repo_files.py /path/to/repo --json
"""

import argparse
import json
import os
from pathlib import Path

# Directories to skip while walking
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

SOURCE_EXTS = {".py", ".js", ".go"}
CONFIG_EXTS = {".yaml", ".yml", ".json", ".toml"}


def is_test_file(path: Path) -> bool:
    """Detect common test-file naming conventions across languages."""
    name = path.name.lower()
    parts = {p.lower() for p in path.parts}

    if "test" in parts or "tests" in parts or "__tests__" in parts:
        return True
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    if name.endswith((".test.js", ".spec.js", "_test.go")):
        return True
    return False


def is_docs_file(path: Path) -> bool:
    name = path.name.lower()
    return name.startswith("readme") or path.suffix.lower() == ".md"


def tag_file(path: Path) -> str:
    """Return a single tag for a given file path. Tests take priority
    over source, since a *_test.py file is still a .py source file."""
    if is_test_file(path):
        return "test"
    if is_docs_file(path):
        return "docs"
    ext = path.suffix.lower()
    if ext in SOURCE_EXTS:
        return "source"
    if ext in CONFIG_EXTS:
        return "config"
    return "other"


def walk_repo(root: str):
    """Yield (Path, tag) for every file under root, skipping noisy dirs."""
    root_path = Path(root)
    for dirpath, dirnames, filenames in os.walk(root_path):
        # prune noisy directories in-place so os.walk doesn't descend into them
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            rel = fpath.relative_to(root_path)
            yield rel, tag_file(rel)


def main():
    parser = argparse.ArgumentParser(description="Tag repo files by type.")
    parser.add_argument("root", help="Path to the repository root")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of grouped text")
    args = parser.parse_args()

    if not Path(args.root).is_dir():
        raise SystemExit(f"Error: '{args.root}' is not a directory")

    results = list(walk_repo(args.root))

    if args.json:
        payload = [{"path": str(p), "tag": t} for p, t in sorted(results, key=lambda x: str(x[0]))]
        print(json.dumps(payload, indent=2))
        return

    grouped = {}
    for path, tag in results:
        grouped.setdefault(tag, []).append(path)

    order = ["source", "docs", "config", "test", "other"]
    for tag in order:
        files = grouped.get(tag, [])
        if not files:
            continue
        print(f"\n[{tag.upper()}] ({len(files)})")
        for f in sorted(files, key=str):
            print(f"  {f}")

    print(f"\nTotal files: {len(results)}")


if __name__ == "__main__":
    main()