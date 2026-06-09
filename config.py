"""
Global configuration — import this in any pipeline file instead of
repeating constants across modules.
"""

# --- Paths ---
DOCUMENTS_DIR = "documents/cleaned"
CHROMA_DIR = "./chroma_db"

# --- ChromaDB ---
COLLECTION_NAME = "avila_policies"

# --- Embedding model ---
EMBED_MODEL = "all-MiniLM-L6-v2"

# --- Chunking ---
CHUNK_SIZE = 600
OVERLAP = 80
MIN_CHUNK_SIZE = 150

# --- Retrieval ---
TOP_K = 5
DISTANCE_THRESHOLD = 1.2

# --- LLM ---
LLM_MODEL = "llama-3.3-70b-versatile"
