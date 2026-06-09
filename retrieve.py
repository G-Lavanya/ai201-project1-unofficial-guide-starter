import chromadb
from chromadb.utils import embedding_functions
from config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL, TOP_K, DISTANCE_THRESHOLD

_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL
)
_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)


def get_collection():
    """Return the ChromaDB collection. Used by ingest.py."""
    return _collection


def retrieve(query, n_results=TOP_K):
    """
    Find the most relevant policy chunks for a user's question.

    Returns a list of dicts, each with:
      - "text"        : the chunk text
      - "source"      : the document filename
      - "chunk_index" : position of the chunk within its document
      - "distance"    : similarity score (lower = more similar for cosine)
    """
    if _collection.count() == 0:
        return []

    results = _collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    chunks = [
        {
            "text": doc,
            "source": meta.get("source"),
            "chunk_index": meta.get("chunk_index"),
            "distance": dist,
        }
        for doc, meta, dist in zip(documents, metadatas, distances)
        if dist <= DISTANCE_THRESHOLD
    ]

    print(f"Retrieved {len(chunks)} chunks for query: '{query}'")
    for chunk in chunks:
        print(f"[{chunk['source']}] (dist: {chunk['distance']:.3f}) {chunk['text'][:80]}")

    return chunks
