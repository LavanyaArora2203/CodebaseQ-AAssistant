#!/usr/bin/env python3
"""
build_index.py

End-to-end pipeline: walk a repo, chunk every .py/.md file (via
ts_chunker.chunk_file), batch-embed every chunk (via embeddings.py), and
insert vector + metadata into a local FAISS-backed VectorStore
(vector_store.py). Also exposes a `query` subcommand to search the index.

Usage:
    # Build (or rebuild) an index from a directory of source files
    python build_index.py build /path/to/repo --index-path ./index/repo_index

    # Query it
    python build_index.py query ./index/repo_index "parse a config file" --top-k 5

    # Query with a metadata filter (only functions, only python)
    python build_index.py query ./index/repo_index "retry logic" \\
        --chunk-type function --language python

By default this uses LocalHashingEmbedder (no model download, fully
offline) so the pipeline is runnable anywhere. Pass --model <hf-model-name>
to use a real sentence-transformers model instead (requires network access
to Hugging Face) — e.g. --model BAAI/bge-small-en-v1.5
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Optional

from chunking.ast_chunker import chunk_file, Chunk
from embeddings import Embedder, SentenceTransformerEmbedder, LocalHashingEmbedder, batch_embed_chunks
from vector_store import VectorStore

SUPPORTED_SUFFIXES = {".py", ".md"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def collect_chunks(root: str) -> List[Chunk]:
    """Walk `root` and chunk every supported file, skipping noisy dirs."""
    all_chunks: List[Chunk] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            try:
                all_chunks.extend(chunk_file(fpath))
            except Exception as e:
                print(f"  [skip] {fpath}: {e}")
    return all_chunks


def build_embedder(model_name: Optional[str]) -> Embedder:
    if model_name:
        return SentenceTransformerEmbedder(model_name)
    return LocalHashingEmbedder(dim=256)


def build_index(root: str, index_path: str, model_name: Optional[str] = None) -> VectorStore:
    print(f"Walking '{root}' for .py/.md files...")
    chunks = collect_chunks(root)
    print(f"Found {len(chunks)} chunk candidates.")

    embedder = build_embedder(model_name)
    print(f"Embedding with: {getattr(embedder, 'name', type(embedder).__name__)}")
    embedded = batch_embed_chunks(chunks, embedder, batch_size=32)

    store = VectorStore(dim=embedder.dim)
    n_inserted = store.insert(embedded)
    print(f"Inserted {n_inserted} vectors (dim={embedder.dim}) into the store.")

    Path(index_path).parent.mkdir(parents=True, exist_ok=True)
    store.save(index_path)
    print(f"Saved index to {index_path}.faiss / {index_path}.meta.json")

    # Persist which embedder produced this index so `query` can reconstruct
    # a compatible one later — including the fitted state for the offline
    # LocalHashingEmbedder, whose vector space depends on the corpus it saw.
    marker_path = Path(index_path).with_suffix(".embedder.txt")
    if model_name:
        marker_path.write_text(model_name)
    else:
        marker_path.write_text("local-hashing")
        embedder.save(str(Path(index_path).with_suffix(".embedder.pkl")))

    return store


def load_query_embedder(index_path: str) -> Embedder:
    marker_path = Path(index_path).with_suffix(".embedder.txt")
    model_name = marker_path.read_text().strip() if marker_path.exists() else "local-hashing"
    if model_name == "local-hashing":
        pkl_path = Path(index_path).with_suffix(".embedder.pkl")
        if not pkl_path.exists():
            raise RuntimeError(
                f"No saved LocalHashingEmbedder state found at {pkl_path}. "
                "Rebuild the index so its fitted vectorizer/SVD gets persisted."
            )
        return LocalHashingEmbedder.load(str(pkl_path))
    return SentenceTransformerEmbedder(model_name)


def run_query(index_path: str, query_text: str, top_k: int, model_name: Optional[str],
              chunk_type: Optional[str], language: Optional[str]) -> None:
    store = VectorStore.load(index_path)
    embedder = build_embedder(model_name) if model_name else load_query_embedder(index_path)
    query_vector = embedder.embed_one(query_text)

    def where(meta: dict) -> bool:
        if chunk_type and meta.get("chunk_type") != chunk_type:
            return False
        if language and meta.get("language") != language:
            return False
        return True

    use_filter = where if (chunk_type or language) else None
    results = store.query(query_vector, top_k=top_k, where=use_filter)

    if not results:
        print("No results.")
        return

    for r in results:
        m = r["metadata"]
        label = f"{m['chunk_type']}"
        if m.get("qualified_name"):
            label += f" '{m['qualified_name']}'"
        print(f"\n[{r['score']:.3f}] {label} — {m['file_path']}:{m['start_line']}-{m['end_line']}")
        preview = r["text"].strip().splitlines()
        print("\n".join(preview[:6]))


def main():
    parser = argparse.ArgumentParser(description="Chunk, embed, and index a repo; query the resulting vector store.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Chunk + embed + index a directory")
    p_build.add_argument("root", help="Directory to walk")
    p_build.add_argument("--index-path", required=True, help="Output path prefix for the index files")
    p_build.add_argument("--model", default=None,
                          help="sentence-transformers model name (omit for offline LocalHashingEmbedder)")

    p_query = sub.add_parser("query", help="Query an existing index")
    p_query.add_argument("index_path", help="Path prefix used with `build --index-path`")
    p_query.add_argument("query_text", help="Natural-language or code query")
    p_query.add_argument("--top-k", type=int, default=5)
    p_query.add_argument("--model", default=None, help="Override embedder model for the query")
    p_query.add_argument("--chunk-type", default=None, help="Filter: function|class|docstring|comment|markdown_section")
    p_query.add_argument("--language", default=None, help="Filter: python|markdown")

    args = parser.parse_args()

    if args.command == "build":
        build_index(args.root, args.index_path, args.model)
    elif args.command == "query":
        run_query(args.index_path, args.query_text, args.top_k, args.model, args.chunk_type, args.language)


if __name__ == "__main__":
    main()
