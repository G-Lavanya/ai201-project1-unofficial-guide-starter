# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

This project covers **Avila University student policies** — academic integrity, disciplinary procedures, housing rules, accommodation requests, financial aid eligibility, and the appeals process.

This knowledge is valuable because the official documents are long PDFs (the Student Handbook alone is 247,000 characters) that students rarely read cover-to-cover. When a specific situation arises — a disciplinary notice, a financial aid warning, a roommate conflict — a student needs the exact policy section fast. The RAG system retrieves that section directly instead of requiring students to navigate three separate PDFs.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Avila University| General student policies and expectations| https://www.avila.edu/wp-content/uploads/2024/04/Student-Handbook-2022-2023-FINAL.pdf|
| 2 |Avila University |This has housing rules| https://www.avila.edu/wp-content/uploads/2024/08/Housing-Handbook-24-25.pdf|
| 3 |Avila University |Avila University community standards are showed here |https://www.avila.edu/wp-content/uploads/2025/06/Community-Standards-and-Expectations-Accountability-Procedures-Final.pdf |
| 4 |Avila University |This explains Anti-hazing policy |https://www.avila.edu/wp-content/uploads/2025/06/Anti-Hazing-policy.pdf |
| 5 |Avila University |Financial aid for graduate students |https://www.avila.edu/avila-life/sleptiza-center-for-student-excellence/student-financial-services/financial-aid-office/financial-aid-for-graduate-students/ |
| 6 | Avila University | International Student Financial Proof and Affidavit of Support|https://www.avila.edu/wp-content/uploads/2024/04/Avila-Undergrad-Affidavit-International-Undergraduate-Version-212.pdf|
| 7 | | | |
| 8 | | | |
| 9 | | | |
| 10 | | | |

---

## Document Cleaning (`clean.py`)

**Script:** `clean.py`
**Input:** `documents/*.txt` (raw text extracted from PDFs)
**Output:** `documents/cleaned/*.txt` (cleaned text, ready for chunking)

The documents are PDFs converted to plain text, which introduces several categories of noise that would degrade embedding quality if left in. `clean.py` runs each file through a series of targeted fixes before any chunking or embedding happens.

| Artifact removed | Example | Reason |
|---|---|---|
| PDF form-feed characters (`\x0c`) | invisible page-break markers between pages | Inserted by PDF-to-text conversion; not part of any policy |
| Lone page numbers | lines containing only `5` or `Page 58` | PDF pagination artifacts that break chunk coherence |
| Private-use Unicode bullets (``, ``) | `` or `` → `-` | Font-specific characters the embedding model cannot interpret meaningfully |
| Smart/curly hyphens and dashes (`‐ ‑ ‒ – —`) | `co‐curricular` → `co-curricular` | Inconsistent tokenization: the same word with two different hyphens would produce different embeddings |
| Decorative arrow bullets (`► ▶ →`) | `►` → `-` | Cosmetic PDF formatting with no semantic value |
| PDF form-field placeholders | `Click here to enter text.` | Unfilled template fields in Housing Handbook; appear in 20 chunks with no policy content |
| Runs of 3+ blank lines | collapsed to 2 | Reduces wasted space inside chunks without losing section structure |

**What is kept:** all substantive policy text, section headers, numbered lists, URLs in contact/resource sections, and middle-dot bullets (∙) used as legitimate list markers in the Community Values section.

**How to run:**
```bash
python clean.py          # writes documents/cleaned/*.txt and prints a sample for review
```

After running `clean.py`, always read the printed sample to confirm no artifacts remain before running `ingest.py`.

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->


Chunk size: 600 characters

Overlap: 80 characters

Reasoning:

The strategy uses **hybrid chunking** — header splitting first, then a sliding character window within each section.

**Step 1 — Header split:** The documents use consistent section headings such as "Level 1:", "Level 2:", "Level 3:", Roman numeral sections (I., II., III.), and ALL-CAPS department names. The pipeline detects these with a regular expression and cuts at each boundary, so every named policy section gets its own chunk with a focused, unmixed semantic identity.

**Step 2 — Sliding window:** Any section longer than 600 characters is sub-split with a 600-character window and 80-character overlap, applied entirely within that section. The overlap preserves continuity at sub-split boundaries without ever crossing a header boundary into a neighbouring section.

**Step 3 — Merge short chunks:** Sub-chunks shorter than 150 characters within the same section are merged with their immediate neighbour, also within the same section, so no chunk ends up with too little content to produce a meaningful embedding.

Why this is better than a pure character window: a fixed 600-character window can straddle two adjacent policy sections (e.g., the tail of Level 2 sanctions and the opening of Level 3), producing a chunk whose embedding is semantically blurry and ranks poorly for level-specific queries. Header splitting eliminates that mixing before windowing begins.
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
Embedding model: all-MiniLM-L6-v2 (Sentence Transformers)

**Top-k:** 5 (updated from initial spec of 3 — see README Failure Case Analysis)

**Production tradeoff reflection:**

I selected all-MiniLM-L6-v2 because it provides a strong balance between semantic retrieval quality, computational efficiency, and ease of local deployment. The model generates 384-dimensional embeddings and performs well for English-language semantic search tasks.

If deploying this system for real users and cost were not a constraint, I would consider several tradeoffs:

Larger embedding models may improve retrieval accuracy for legal and administrative terminology found in university policies.
Models with multilingual capabilities would better support diverse student populations.
Larger context windows would allow more retrieved policy sections to be processed simultaneously.
Higher-capacity models may increase latency, affecting user experience.
Locally hosted models offer stronger privacy and institutional control, while API-hosted models provide easier access to state-of-the-art capabilities with reduced infrastructure requirements.
Evaluation Plan


---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What happens if a student exceeds the allowed absence limit?	Student may face administrative withdrawal or academic penalties according to the attendance policy.| |
| 2 | How should a student report suspected academic misconduct?	The academic integrity policy outlines reporting procedures through designated university offices.| |
| 3 | How can students request pregnancy accommodations?	Students should contact the Student Access Office to request pregnancy-related accommodations.| |
| 4 |What are the requirements to maintain financial aid eligibility?	Students must satisfy satisfactory academic progress requirements defined by the financial aid policy. | |
| 5 | What is the process for appealing a final course grade?	The grading policy specifies the formal grade appeal process and associated deadlines.| |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Policy Fragmentation Across Chunks

Important policy information may span chunk boundaries. Although overlap mitigates this issue, poorly chosen chunk sizes could still separate related information and negatively affect retrieval performance.

2. Off-Topic or Low-Relevance Retrieval

Semantically similar administrative language across policies may cause retrieval of irrelevant policy sections. Distance threshold filtering and careful evaluation are necessary to reduce this risk.



---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
University Policy Documents (.txt — 3 files, ~390k chars total)
        │
        ▼
  clean.py  ──── Remove PDF artifacts (form-feeds, page numbers,
        │         Unicode bullets, smart hyphens, placeholder text)
        │         Output: documents/cleaned/*.txt
        ▼
  ingest.py  ─── Hybrid Chunking:
        │         1. split_on_headers() — regex splits at Level N:,
        │            Roman numerals, ALL-CAPS section names
        │         2. sliding_window() — 600-char / 80-overlap within
        │            each section only (never crosses header boundaries)
        │         3. merge short sub-chunks (< 150 chars) within section
        │         Result: 695 chunks
        │
        ├──── Embed with SentenceTransformer(all-MiniLM-L6-v2)
        │     384-dimensional vectors, local, no API key required
        │
        └──── Store in ChromaDB (PersistentClient, L2 distance)
                    Collection: avila_policies
                         │
                         ▼
                  retrieve.py  ── Encode query → top-k=5 nearest neighbors
                         │        Filter: L2 distance ≤ 1.2
                         │        Return: [{text, source, chunk_index, distance}]
                         │
                         ▼
                  generate / app.py
                         │        Build context string from retrieved chunks
                         │        System prompt: answer from excerpts only,
                         │        fallback if no chunks pass threshold
                         │
                  Groq API (llama-3.3-70b-versatile, temperature=0.0)
                         │
                         ▼
                  Grounded answer + Sources section
```

**Note:** The original spec showed character-window chunking (top-k=3). Both changed during implementation — see Chunking Strategy section and README Failure Case Analysis for the reasons.


## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I will use ChatGPT to generate and review Python functions for loading university policy documents and implementing character-based chunking using the specified chunk size and overlap values. I will provide the Chunking Strategy section as input and verify that the implementation produces correctly structured chunks with appropriate metadata.

**Milestone 4 — Embedding and retrieval:**
I will use ChatGPT and GitHub Copilot to implement embedding generation with all-MiniLM-L6-v2 and storage in ChromaDB. I will provide the Retrieval Approach specifications and verify that retrieved chunks are relevant to evaluation questions and correctly filtered based on similarity thresholds.

**Milestone 5 — Generation and interface:**
I will use ChatGPT to design grounded system prompts and prompt templates that incorporate retrieved policy excerpts. I will verify outputs by testing evaluation questions and confirming that responses remain restricted to retrieved policy information without introducing unsupported claims.


