"""
Ingestion pipeline: load documents -> chunk -> embed -> store in ChromaDB.
Run once to build the vector database: python ingest.py
"""

import os
from config import (
    DOCUMENTS_DIR,
    CHUNK_SIZE, OVERLAP, MIN_CHUNK_SIZE,
)
from retrieve import get_collection


def load_documents():
    """Load all .txt policy documents from the documents folder."""
    documents = []
    for filename in sorted(os.listdir(DOCUMENTS_DIR)):
        if filename.endswith(".txt"):
            filepath = os.path.join(DOCUMENTS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            documents.append({
                "source": filename,
                "text": text,
            })
    print(f"Loaded {len(documents)} document(s): {[d['source'] for d in documents]}")
    return documents


def chunk_document(text, source):
    """
    Split a policy document into chunks ready for embedding.

    Strategy: character-based sliding window with overlap.
      - CHUNK_SIZE: long enough to carry the meaning of a policy section
      - OVERLAP: duplicates a small window at each boundary so a rule that
        spans two chunks can still be retrieved intact
      - MIN_CHUNK_SIZE: filters out whitespace artifacts and short fragments

    Returns a list of dicts, each with:
      - "text"        : the chunk text (str)
      - "source"      : the document filename (str)
      - "chunk_index" : position index within the document (int)
    """
    chunks = []
    counter = 0
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_text = text[start:end].strip()

        if len(chunk_text) >= MIN_CHUNK_SIZE:
            chunks.append({
                "text": chunk_text,
                "source": source,
                "chunk_index": counter,
            })
            counter += 1

        start += CHUNK_SIZE - OVERLAP

    return chunks


def main():
    docs = load_documents()

    collection = get_collection()

    # Clear existing data so we rebuild cleanly
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc["text"], doc["source"]))

    print(f"Total chunks to embed: {len(all_chunks)}")

    collection.add(
        documents=[c["text"] for c in all_chunks],
        ids=[f"{c['source']}_chunk_{c['chunk_index']}" for c in all_chunks],
        metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in all_chunks],
    )

    print(f"\nDone. {len(all_chunks)} chunks indexed and ready for retrieval.")


if __name__ == "__main__":
    main()
