import numpy as np

from bm25_index import BM25Indexer
from vector_store import VectorStore


class HybridRetriever:

    def __init__(self,
                 vector_store,
                 bm25_index,
                 alpha=0.7):

        self.vector_store = vector_store
        self.bm25 = bm25_index

        # weight for vector similarity
        self.alpha = alpha

        # weight for BM25
        self.beta = 1 - alpha

    def normalize(self, scores):

        values = np.array(scores)

        if values.max() == values.min():
            return np.ones(len(values))

        return (values - values.min()) / (
            values.max() - values.min()
        )

    def search(self,
               query,
               embedding,
               top_k=5):

        vector_results = self.vector_store.search(
            embedding,
            top_k=20
        )

        bm25_results = self.bm25.search(
            query,
            top_k=20
        )

        combined = {}

        ##############################
        # Vector results
        ##############################

        vec_scores = [s for _, s in vector_results]
        vec_scores = self.normalize(vec_scores)

        for (doc, _), score in zip(vector_results,
                                   vec_scores):

            combined[doc["id"]] = {
                "doc": doc,
                "vector": score,
                "bm25": 0
            }

        ##############################
        # BM25 results
        ##############################

        bm_scores = [s for _, s in bm25_results]
        bm_scores = self.normalize(bm_scores)

        for (doc, _), score in zip(
                bm25_results,
                bm_scores):

            if doc["id"] not in combined:

                combined[doc["id"]] = {
                    "doc": doc,
                    "vector": 0,
                    "bm25": score
                }

            else:

                combined[doc["id"]]["bm25"] = score

        ##############################
        # Weighted Fusion
        ##############################

        final = []

        for item in combined.values():

            score = (
                self.alpha * item["vector"] +
                self.beta * item["bm25"]
            )

            final.append(
                (
                    item["doc"],
                    score
                )
            )

        final.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return final[:top_k]