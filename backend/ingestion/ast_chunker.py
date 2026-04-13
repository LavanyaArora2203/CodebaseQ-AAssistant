from typing import List, Dict
from backend.ingestion.metadata_extractor import extract_metadata  # ✅ no duplicate logic


def chunk_python_file(file_path: str, content: str) -> List[Dict]:
    """Delegate to metadata_extractor for Python files."""
    return extract_metadata(file_path, content)


def chunk_documents(documents: List[Dict]) -> List[Dict]:
    """
    Takes repo_loader output and returns AST chunks.
    Python files → AST chunked.
    Other files  → kept as single chunk.
    """
    all_chunks = []

    for doc in documents:
        content = doc["content"]
        metadata = doc["metadata"]
        file_path = metadata.get("file") or metadata.get("file_path", "unknown")

        if file_path.endswith(".py"):
            chunks = chunk_python_file(file_path, content)
            if chunks:
                all_chunks.extend(chunks)
            else:
                all_chunks.append(doc)  # fallback if AST fails
        else:
            all_chunks.append({
                "content": content,
                "metadata": {
                    "file": file_path,
                    "function": None,
                    "class": None,
                    "type": "file",
                    "imports": [],
                    "calls": [],
                    "docstring": ""
                }
            })

    print(f"[INFO] Generated {len(all_chunks)} chunks")
    return all_chunks


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from backend.ingestion.repo_loader import load_github_repo

    repo_url = input("Enter GitHub Repo URL: ").strip()
    docs = load_github_repo(repo_url)
    chunks = chunk_documents(docs)

    print("\n[SAMPLE CHUNK]")
    if chunks:
        s = chunks[0]
        print("File:", s["metadata"]["file"])
        print("Type:", s["metadata"]["type"])
        print("Function:", s["metadata"]["function"])
        print("Calls:", s["metadata"]["calls"])
        print("Preview:\n", s["content"][:300])