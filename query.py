"""
Retrieval pipeline: given a user query, find the top-k most relevant chunks
from ChromaDB using semantic similarity, then print them with source attribution.

Usage:
    python query.py "What happens if a student misses too many classes?"
    python query.py  # interactive mode
"""

import sys
import chromadb
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "avila_policies"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 3
DISTANCE_THRESHOLD = 1.2  # lower distance = more similar; ChromaDB uses squared L2 by default


def retrieve(query: str, collection, model: SentenceTransformer, top_k: int = TOP_K):
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({"text": doc, "source": meta["source"], "chunk_index": meta["chunk_index"], "distance": dist})

    # Filter out low-relevance chunks
    relevant = [c for c in chunks if c["distance"] <= DISTANCE_THRESHOLD]
    return relevant


def display_results(query: str, chunks: list[dict]):
    print(f"\nQuery: {query}")
    print("=" * 60)
    if not chunks:
        print("No relevant policy excerpts found above the similarity threshold.")
        print("Please contact university administration for this information.")
        return

    for i, chunk in enumerate(chunks, 1):
        print(f"\n[Result {i}] Source: {chunk['source']} | Chunk: {chunk['chunk_index']} | Distance: {chunk['distance']:.4f}")
        print("-" * 60)
        print(chunk["text"].strip())

    print("\n" + "=" * 60)
    print("Sources:")
    for chunk in chunks:
        print(f"  - {chunk['source']} (chunk {chunk['chunk_index']})")


def main():
    print(f"Loading embedding model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(COLLECTION_NAME)

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        chunks = retrieve(query, collection, model)
        display_results(query, chunks)
    else:
        print("Interactive mode — type a question or 'quit' to exit.\n")
        while True:
            query = input("Question: ").strip()
            if query.lower() in ("quit", "exit", "q"):
                break
            if not query:
                continue
            chunks = retrieve(query, collection, model)
            display_results(query, chunks)


if __name__ == "__main__":
    main()
