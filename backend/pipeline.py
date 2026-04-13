# backend/pipeline.py

from typing import List, Dict

from backend.ingestion.repo_loader import load_github_repo
from backend.ingestion.ast_chunker import chunk_documents

from backend.retrieval.vector_store import store_chunks
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.query_classifier import classify_query

from backend.llm.llm_client import generate_answer
from backend.llm.prompts import get_prompt


# -----------------------------
# INGESTION PIPELINE
# -----------------------------
def ingest_repo(repo_url: str) -> List[Dict]:
    """
    Full ingestion:
    1. Load repo files
    2. AST chunk (handles metadata extraction internally)
    3. Store in ChromaDB
    """

    print("\n[STEP 1] Loading repo...")
    documents = load_github_repo(repo_url)
    print(f"[INFO] Loaded {len(documents)} raw files")

    # ✅ chunk_documents handles both Python AST chunking
    # and non-Python fallback internally — no need to call
    # extract_metadata separately (that caused double processing)
    print("\n[STEP 2] Chunking...")
    final_chunks = chunk_documents(documents)
    print(f"[INFO] Final chunks: {len(final_chunks)}")

    print("\n[STEP 3] Storing in ChromaDB...")
    store_chunks(final_chunks)

    return final_chunks


# -----------------------------
# QUERY PIPELINE
# -----------------------------
class RAGPipeline:
    def __init__(self, chunks: List[Dict]):
        self.retriever = HybridRetriever(chunks)

    def run(self, query: str, top_k: int = 5) -> Dict:
        """Full query → answer pipeline."""

        print("\n[STEP 1] Classifying query...")
        query_type = classify_query(query)
        print(f"[INFO] Query type: {query_type}")

        print("\n[STEP 2] Retrieving context...")
        retrieved_chunks = self.retriever.retrieve(query, top_k)
        context = self._build_context(retrieved_chunks)

        print("\n[STEP 3] Generating answer...")
        prompt = get_prompt(query, context, query_type)
        answer = generate_answer(prompt)

        return {
            "query": query,
            "query_type": query_type,
            "answer": answer,
            "sources": retrieved_chunks
        }

    def _build_context(self, chunks: List[Dict]) -> str:
        context_parts = []
        for chunk in chunks:
            meta = chunk["metadata"]
            context_parts.append(
                f"FILE: {meta.get('file')}\n"
                f"TYPE: {meta.get('type')}\n"
                f"FUNCTION: {meta.get('function')}\n"
                f"CLASS: {meta.get('class')}\n\n"
                f"CODE:\n{chunk['content']}"
            )
        return "\n\n---\n\n".join(context_parts)


# -----------------------------
# TEST RUN
# -----------------------------
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    repo_url = input("Enter GitHub Repo URL: ").strip()

    chunks = ingest_repo(repo_url)
    rag = RAGPipeline(chunks)

    print("\n[READY] Ask questions about the repo")
    while True:
        query = input("\nAsk: ")
        result = rag.run(query)
        print("\n[ANSWER]\n", result["answer"])
        print("\n[SOURCES]")
        for src in result["sources"]:
            print("-", src["metadata"].get("file"))