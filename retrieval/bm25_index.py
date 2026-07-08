from rank_bm25 import BM25Okapi
import pickle
import json


class BM25Indexer:

    def __init__(self):
        self.bm25 = None
        self.documents = []

    def tokenize(self, text: str):
        return text.lower().replace("_", " ").split()

    def build(self, chunks):

        corpus = []

        for chunk in chunks:

            searchable = " ".join([
                chunk.get("function_name", ""),
                chunk.get("file_name", ""),
                chunk.get("content", "")
            ])

            corpus.append(self.tokenize(searchable))

        self.bm25 = BM25Okapi(corpus)
        self.documents = chunks

    def search(self, query, top_k=10):

        tokens = self.tokenize(query)

        scores = self.bm25.get_scores(tokens)

        ranked = sorted(
            zip(self.documents, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return ranked[:top_k]

    def save(self, path):

        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path):

        with open(path, "rb") as f:
            return pickle.load(f)