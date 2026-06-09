import os
from groq import Groq
from dotenv import load_dotenv
from config import LLM_MODEL

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = (
    "You are a university policy assistant for Avila University. "
    "Answer student questions using only the policy excerpts provided and also provide source attribution for each excerpt. "
    "If the excerpts do not contain enough information, say: "
    "'I don't have information about that in the retrieved policy documents. "
    "Please contact Avila University administration directly.' "
)


def generate_response(query: str, retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        return (
            "I don't have information about that in the retrieved policy documents. "
            "Please contact Avila University administration directly."
        )

    context = "\n\n".join(
        f"[Excerpt {i} — {c['source']}]\n{c['text'].strip()}"
        for i, c in enumerate(retrieved_chunks, 1)
    )

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Policy excerpts:\n\n{context}\n\nStudent question: {query}"},
        ],
        temperature=0.0,
    )

    answer = response.choices[0].message.content.strip()

    if "Sources:" not in answer:
        sources = sorted({c["source"] for c in retrieved_chunks})
        answer += "\n\nSources:\n" + "\n".join(f"  - {s}" for s in sources)

    return answer
