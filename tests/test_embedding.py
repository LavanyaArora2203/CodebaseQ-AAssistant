from embeddings.embeddings import SentenceTransformerEmbedder

embedder = SentenceTransformerEmbedder(
    model_name="BAAI/bge-small-en-v1.5"
)

texts = [
    "def add(a, b): return a+b",
    "def subtract(a, b): return a-b"
]

vectors = embedder.embed(texts)

print(vectors.shape)
print(vectors[0][:10])