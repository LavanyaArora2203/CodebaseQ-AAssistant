# backend/retrieval/vector_store.py

import uuid
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "backend/chroma_db"
COLLECTION_NAME = "codebase"


def get_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection():
    client = get_client()
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )
    return collection


def clean_metadata(metadata: Dict) -> Dict:
    cleaned = {}
    for key, value in metadata.items():
        if isinstance(value, list):
            cleaned[key] = ", ".join(map(str, value))
        elif value is None:
            cleaned[key] = ""
        else:
            cleaned[key] = value
    return cleaned


def store_chunks(chunks: List[Dict]):
    collection = get_collection()
    ids, documents, metadatas = [], [], []

    for chunk in chunks:
        metadata = clean_metadata(chunk["metadata"])
        file_name = metadata.get("file", "unknown")
        func = metadata.get("function", "chunk")
        unique_id = f"{file_name}:{func}:{uuid.uuid4()}"
        ids.append(unique_id)
        documents.append(chunk["content"])
        metadatas.append(metadata)

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"[INFO] Stored {len(chunks)} chunks in ChromaDB")


def query_chunks(query: str, n_results: int = 5, filters: Dict = None):
    collection = get_collection()

    # ✅ only pass where= if filters is actually set — None causes Chroma error
    query_kwargs = {
        "query_texts": [query],
        "n_results": n_results
    }
    if filters:
        query_kwargs["where"] = filters

    return collection.query(**query_kwargs)


def reset_collection():
    client = get_client()
    client.delete_collection(name=COLLECTION_NAME)
    print("[INFO] Collection reset")


def get_collection_count():
    return get_collection().count()


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from backend.pipeline import run_pipeline

    repo_url = input("Enter GitHub Repo URL: ").strip()
    print("\n[STEP 1] Ingest + Chunk...")
    chunks = run_pipeline(repo_url)

    print("\n[STEP 2] Store in Chroma...")
    store_chunks(chunks)

    print("\n[STEP 3] Query test")
    q = input("Ask: ")
    res = query_chunks(q)

    print("\n[RESULTS]")
    for i, doc in enumerate(res["documents"][0]):
        print(f"\n--- Result {i+1} ---")
        print(doc[:300])