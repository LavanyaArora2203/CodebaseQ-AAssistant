# backend/retrieval/hybrid_retriever.py

from typing import List, Dict
from rank_bm25 import BM25Okapi
from backend.retrieval.vector_store import query_chunks


class BM25Retriever:
    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks
        self.corpus = [chunk["content"] for chunk in chunks]
        self.tokenized_corpus = [doc.split() for doc in self.corpus]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        tokenized_query = query.split()
        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]
        return [self.chunks[i] for i in ranked_indices]


class HybridRetriever:
    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks
        self.bm25 = BM25Retriever(chunks)
        self.content_map = {chunk["content"]: chunk for chunk in chunks}

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        # 1. Semantic search via ChromaDB
        vector_results = query_chunks(query, n_results=top_k)
        semantic_docs = vector_results.get("documents", [[]])[0]
        semantic_chunks = [
            self.content_map[doc]
            for doc in semantic_docs
            if doc in self.content_map
        ]

        # 2. Keyword search via BM25
        keyword_chunks = self.bm25.search(query, top_k)

        # 3. Merge — semantic first, then BM25, deduplicated
        combined = []
        for chunk in semantic_chunks + keyword_chunks:
            if chunk not in combined:
                combined.append(chunk)

        return combined[:top_k]

    # ✅ indented inside class now
    def retrieve_with_filter(self, query: str, top_k: int = 5, type_filter: str = None) -> List[Dict]:
        results = self.retrieve(query, top_k * 2)
        if type_filter:
            results = [
                r for r in results
                if r["metadata"].get("type") == type_filter
            ]
        return results[:top_k]


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from backend.pipeline import run_pipeline

    repo_url = input("Enter GitHub Repo URL: ").strip()
    print("\n[STEP 1] Ingesting repo...")
    chunks = run_pipeline(repo_url)

    retriever = HybridRetriever(chunks)

    print("\n[STEP 2] Ask questions")
    while True:
        query = input("\nAsk: ")
        results = retriever.retrieve(query)
        print("\n[RESULTS]")
        for i, r in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print("File:", r["metadata"].get("file"))
            print("Type:", r["metadata"].get("type"))
            print("Preview:\n", r["content"][:300])