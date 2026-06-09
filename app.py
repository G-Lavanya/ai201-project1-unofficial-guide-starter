"""
Gradio web interface for the Avila University Policy Assistant.

Run:
    python app.py
Then open http://localhost:7860 in your browser.
"""

import os
import gradio as gr
from dotenv import load_dotenv
from groq import Groq
from retrieve import retrieve
from ingest import main as run_ingest
from config import LLM_MODEL, TOP_K, COLLECTION_NAME, CHROMA_DIR
import chromadb

load_dotenv()

SYSTEM_PROMPT = """You are a university policy assistant for Avila University.
Your ONLY job is to answer student questions using the policy excerpts provided below.

Rules you must follow without exception:
1. Base your answer solely on the provided excerpts. Do not use your general training knowledge.
2. If the excerpts do not contain enough information to answer the question, respond with exactly:
   "I don't have information about that in the retrieved policy documents. Please contact Avila University administration directly."
3. Do not speculate, infer, or fill gaps with outside knowledge.
4. Be concise and direct. Quote or paraphrase the relevant policy language.
5. Always end your response with a Sources section listing the document(s) you drew from."""


# ---------------------------------------------------------------------------
# Ingestion — runs once on startup, skipped if already populated
# ---------------------------------------------------------------------------

def run_ingestion():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        col = client.get_collection(COLLECTION_NAME)
        if col.count() > 0:
            print(f"Vector store already populated ({col.count()} chunks). Skipping ingestion.")
            print("To re-ingest, delete the ./chroma_db folder and restart.")
            return
    except Exception:
        pass

    print("Ingesting policy documents...")
    run_ingest()


# ---------------------------------------------------------------------------
# Load models
# ---------------------------------------------------------------------------

run_ingestion()

api_key = os.getenv("GROQ_API_KEY")
if not api_key or api_key == "your_key_here":
    raise RuntimeError("GROQ_API_KEY is not set in .env")
groq_client = Groq(api_key=api_key)

print("Ready.\n")


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[Excerpt {i} — {chunk['source']}]\n{chunk['text'].strip()}")
    return "\n\n".join(parts)


def chat(message, history):
    message = message.strip()
    if not message:
        return ""

    chunks = retrieve(message, n_results=TOP_K)

    if not chunks:
        return (
            "I don't have information about that in the retrieved policy documents. "
            "Please contact Avila University administration directly."
        )

    context = build_context(chunks)
    user_message = f"Policy excerpts:\n\n{context}\n\nStudent question: {message}"

    response = groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks() as demo:

    gr.HTML("""
        <div style="text-align:center; padding:1.25rem 0 0.5rem;">
            <h1 style="font-size:2rem; font-weight:700; color:#1e3a5f; margin:0;">
                Avila University Policy Assistant
            </h1>
            <p style="color:#6b7280; font-size:1rem; margin:0.4rem 0 0;">
                Ask questions about student policies — answers grounded strictly in official documents.
            </p>
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            gr.ChatInterface(
                fn=chat,
                chatbot=gr.Chatbot(height=460),
                textbox=gr.Textbox(
                    placeholder='e.g. "How do I appeal a disciplinary decision?"',
                    container=False,
                    scale=7,
                ),
                examples=[
                    "How should a student report suspected academic misconduct?",
                    "How can students request pregnancy accommodations?",
                    "What are the requirements to maintain financial aid eligibility?",
                    "What is the process for appealing a disciplinary decision?",
                    "What happens if a student is found responsible for a Level 3 offense?",
                ],
                cache_examples=False,
            )

        with gr.Column(scale=1, min_width=200):
            gr.HTML("""
                <div style="background:#f0f4ff; border:1px solid #c7d2fe;
                            border-radius:10px; padding:1rem; margin-top:0.5rem;">
                    <p style="font-size:0.8rem; font-weight:700; color:#1e3a5f;
                               margin:0 0 0.5rem; letter-spacing:0.05em;">
                        LOADED POLICY DOCUMENTS
                    </p>
                    <ul style="font-size:0.85rem; color:#1e40af; list-style:none;
                                padding:0; margin:0; line-height:2;">
                        <li>Student Handbook 2022-23</li>
                        <li>Housing Handbook 24-25</li>
                        <li>Community Standards &amp; Accountability</li>
                    </ul>
                    <hr style="border:none; border-top:1px solid #c7d2fe; margin:0.75rem 0;">
                    <p style="font-size:0.75rem; color:#3730a3; margin:0; line-height:1.5;">
                        Answers are grounded in the loaded documents only.
                        If a policy is not in these documents, the assistant will say so.
                    </p>
                </div>
            """)


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Avila Policy Assistant — starting up")
    print("=" * 50 + "\n")
    demo.launch(theme=gr.themes.Soft(primary_hue="blue"))
