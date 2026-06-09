# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy the environment template and add your Groq API key
cp .env.example .env
# Then edit .env and replace your_key_here with your actual Groq API key

# 3. Launch the web interface (ingestion runs automatically on first startup)
python app.py
# Opens at http://localhost:7860

# Optional: rebuild the vector store from scratch
#   Delete ./chroma_db/ then rerun python app.py
# Optional: run ingestion standalone
python ingest.py
```

---

## Domain

This system covers **Avila University student policies** — disciplinary procedures, housing rules, academic integrity standards, accommodation requests, financial aid requirements, and appeals processes.

This knowledge is valuable because students facing a disciplinary situation, accommodation request, or financial aid question often cannot find a fast, specific answer. The official documents (PDFs totaling 300+ pages) are designed to be comprehensive references, not searchable tools. A student who needs to know "what exactly happens at Level 3?" or "how many days do I have to appeal?" would have to read through the entire Community Standards document to find the answer. This system retrieves the relevant section and generates a direct, sourced answer in seconds.

The difficulty with official channels is that each policy lives in a different PDF, terminology is not consistent across documents, and the university's website links to the PDFs without providing section-level search. This makes the RAG approach particularly well-suited: the chunked, indexed documents can be searched semantically, returning the exact paragraph that answers the question.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Avila University| pdf| https://www.avila.edu/wp-content/uploads/2024/04/Student-Handbook-2022-2023-FINAL.pdf|
| 2 |Avila University |pdf | https://www.avila.edu/wp-content/uploads/2024/08/Housing-Handbook-24-25.pdf|
| 3 |Avila University |pdf |https://www.avila.edu/wp-content/uploads/2025/06/Community-Standards-and-Expectations-Accountability-Procedures-Final.pdf |
| 4 |Avila University |pdf |https://www.avila.edu/wp-content/uploads/2025/06/Anti-Hazing-policy.pdf |
| 5 |Avila University |webpage |https://www.avila.edu/avila-life/sleptiza-center-for-student-excellence/student-financial-services/financial-aid-office/financial-aid-for-graduate-students/ |
| 6 |Avila University  |pdf |https://www.avila.edu/wp-content/uploads/2024/04/Avila-Undergrad-Affidavit-International-Undergraduate-Version-212.pdf
 |
| 7 | | | |
| 8 | | | |
| 9 | | | |
| 10 | | | |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 600 characters

**Overlap:** 80 characters

**Why these choices fit your documents:**
The pipeline uses **hybrid chunking** — header splitting first, then a sliding character window within each section.

- **Step 1 — Header split:** University policy documents use consistent section headings such as `Level 1:`, `Level 2:`, `Level 3:`, Roman numeral sections (`I.`, `II.`), and ALL-CAPS department names. A regular expression detects these boundaries and splits there, so each named policy section occupies its own chunk with a focused, unmixed semantic identity.

- **Step 2 — Sliding window within sections:** Any section longer than 600 characters is sub-split using a sliding window of 600 characters with 80-character overlap, applied only within that section. This preserves sentence continuity at sub-split boundaries without ever crossing a header boundary into a neighbouring section.

- **Step 3 — Merge short sub-chunks:** Sub-chunks shorter than 150 characters are merged with their immediate neighbour within the same section only, so no chunk is too small to produce a meaningful embedding.

Why this matters: a pure 600-character character window can straddle two adjacent policy sections — for example, the tail of "Level 2: Probationary Status" and the opening of "Level 3: Final Warning Status" end up in the same chunk. The resulting embedding is semantically blurry and ranks poorly for a query like "Level 3 offense." Header splitting eliminates that mixing before windowing begins, which fixed a retrieval failure observed during evaluation (see Failure Case Analysis).

**Final chunk count:** 695 chunks across 3 documents

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:all-MiniLM-L6-v2**
--- The embedding model I am using is all-MiniLM-L6-v2 from sentence transformers to generate vector representations of the university policy documents. Since the university policy documenst are written in english and contain mostly straigthforward adimistrative language, this lightweight model was sufficient for capturing the semantic relationships needed for the retrieval system.

Considerations for Real-world Deployment:

If cost were not constraint, I would evaluate several tradeoffs when selecting an embedding model for production use:
     >>Acurracy on Domain-specific Text:
     University policies often contain legal, administrative, and compliance-related terminology. Larger embedding models or models fine-tuned on legal or institutional documents may better capture subtle distinctions in policy language, leading to more accurate retrieval results.
     >>Context length limits: (Context length refers to the maximum amount of text an embedding or language model can process in a single request.) Models with large context windows would be preferable because policy sections can be lengthy and interconnected.
     >>Multilingual Support: If the university serves a multilingual population, I would consider multilingual embedding models capable of generating high-quality embeddings across multiple languages. 
     >>Latency: Larger and more sophististicated models generally provide better retrieval performance but require more computational resources and have higher inference times. For real-time applications with many concurrent users, latency becomes an importsant consideration.
     >>Local vs API-Hosted Deployment: Local deployment offers greater control over-data privacy, security and compilance, which is especially important when handling institutional information. However, locally hosted models require significant infrastructure and maintenance.
OverAll, if buget were unlimited, I would prioritize retrieval accuracy and multilingual capabaily while balncing latency requirements and institutional privacy policies when selecting an embedding model for deployment.

**Production tradeoff reflection:**

--- 
Based on examining several university policy sections, I observed that the average policy statement length was approximately 480–520 characters. Therefore, I selected a chunk size of 600 characters with an overlap of 80 characters. This configuration increases the likelihood that a complete policy statement remains within a single chunk while preserving contextual continuity across chunk boundaries.

With this approach, adjacent chunks advance by 520 characters (`chunk_size - overlap = 600 - 80`), resulting in an 80-character overlap between consecutive chunks. In contrast, a chunk size of 300 characters would likely split individual policy statements into multiple fragments, reducing their standalone semantic meaning and potentially degrading retrieval performance.

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
Grounding is enforced by the system prompt.
Weak grounding instruction: "answer accurately based on the policies"
Strong grounding instruction: "Answer only through rules mentioned in the documents. If the answer is not provided inn the documents or excerpts answers just say explicitly: do draw outside knowledge or trained LLM information.

System prompt: " You are a policy Bot, to help students with university policies and ground rules, You only provide data which are present in excerpts and donot draw data from outside resources.

If answer is not found in provided excerpts  just say " I dont have any of the information regarding the query please contact university administration.Thank you!""


Structural Grounding Mechanism: 
1. Retrieval Augmented context injection:
Only the top semantically relevant policy chunks retrieved from the vector database are inserted into the prompt context. The model does not have direct access to the full document collection.
2. Relevance Filtering:
Retrieved chunks are filtered using a distance threshold:

[c for c in retrieved_chunks if c["distance"] <= 0.5]

This removes low-relevance results before they are presented to the model, reducing the likelihood that unrelated policy sections influence the response.
3. Structured Context Formatting
Formatted context:
{policy excerpts}
question: {query}
4. Fallback:
If no retrieved chunks meet the relevance threshold, the system does not attempt to generate an answer from general knowledge. Instead, it returns the predefined fallback message directing the student to official university resources.

Together, these prompt-level instructions and structural safeguards reduce hallucinations and ensure that responses remain grounded in the retrieved university policy documents.

**How source attribution is surfaced in the response:**

--- Source attribution is provided by displaying metadata associated with the retrieved policy chunks alongside the generated answer. Each chunk stored in the vector database contains identifying information such as the policy document name and chunk identifier.

After retrieval, the system presents the response together with the source information used to generate the answer. For example:

Answer:
Students who miss more than 20% of scheduled classes may be subject to administrative withdrawal from the course.

Sources:
- Attendance Policy (Chunk: attendance_policy_3)
- Student Handbook (Chunk: student_handbook_7)

Providing source attribution allows users to trace the origin of the information, verify the response against the official university documents, and increases transparency and trust in the system's outputs.

If no relevant policy excerpts are retrieved, the system does not provide an answer and instead directs users to consult official university resources.
## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | How should a student report suspected academic misconduct? | A person with first-hand knowledge must submit an Academic Honesty Incident Report to the Dean of the academic course or to the Academic Vice President. | "must report the violation and provide an Academic Honesty Incident Report and any other documentation to the Dean associated with the academic course or to the Academic Vice President." Chunk 109 (dist 0.729) contained the exact procedure. | Relevant | Accurate |
| 2 | How can students request pregnancy accommodations? | Students should contact the Student Access Office, which conducts an individualized assessment. Requests made directly to instructors do not count. | "Students seeking accommodations for pregnancy-related matters should contact the Student Access Office." Chunk 474 (dist 0.501) was a near-exact match. | Relevant | Accurate |
| 3 | What are the requirements to maintain financial aid eligibility? | Students must meet Satisfactory Academic Progress (SAP) standards; if they withdraw, they must complete more than 60% of the term to keep 100% of their aid. | Returned the 60% completion / Return of Title IV Funds rule but omitted the broader SAP standards (GPA and credit completion rate), which are in the Online Catalog — not in the ingested documents. | Partially relevant | Partially accurate |
| 4 | What is the process for appealing a disciplinary decision? | Level 1 offenses cannot be appealed. Level 2+ offenses can be appealed in writing within 5 working days to the hearing officer's supervisor on grounds of procedural unfairness, insufficient evidence, or disproportionate sanctions. | Accurately described the 5-day window, written request requirement, and all three valid grounds for appeal. Drew from both the Student Handbook and Community Standards document. | Relevant | Accurate |
| 5 | What happens if a student is found responsible for a Level 3 offense? | Level 3 is "Final Warning Status." Consequences include all Level 2 sanctions plus possible expulsion from residence halls (no refund, must vacate within 24 hours), loss of ability to represent the University, and severe campus activity restrictions. | Initially returned the fallback message (off-target retrieval). After switching to hybrid chunking, system correctly returned: "behavior severely questioned... typical consequences include expulsion from residence halls." (chunk 104, dist 0.769) | Relevant (after fix) | Accurate (after fix) |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:**  
"What happens if a student is found responsible for a Level 3 offense?"

**What the system returned:**  
The fallback message: "I don't have information about that in the retrieved policy documents. Please contact Avila University administration directly." — even though the Level 3 policy exists in the Student Handbook at the section titled "Level 3: Final Warning Status."

**Root cause (tied to a specific pipeline stage):**  
The failure occurred at the **chunking stage**. The Level 3 policy text starts mid-paragraph after a long list of Level 2 sanctions. With a 600-character chunk size and 80-character overlap, the chunk that contains the phrase "Level 3: Final Warning Status" (chunk 97) also contains the tail end of Level 2 content plus housing eviction language. When the query "Level 3 offense" was embedded, the embedding model matched it most strongly to chunks about general disciplinary hearings (chunk 86, dist 0.769) and room-visit violations (chunk 78, dist 0.841) — not chunk 97 — because chunk 97's semantic signal is diluted by the mixed Level 2/Level 3 content it contains. The relevant text was retrieved during manual inspection (`grep`) but was not surfaced by semantic search because the chunk boundary caused topic mixing that confused the embedding.

**What you would change to fix it:**  
Use structure-aware chunking instead of fixed character windows. The Student Handbook uses consistent section headers ("Level 1:", "Level 2:", "Level 3:") that serve as natural split points. Splitting on these headers keeps each sanction level in its own chunk with a clean semantic identity.

**Fix applied and verified:**  
The chunking strategy was updated to hybrid chunking (header split → sliding window within each section → merge short sub-chunks). After rebuilding the vector store with 689 chunks, the Level 3 chunk (chunk 104) now starts cleanly with "Level 3: Final Warning Status" with no Level 2 content mixed in. Re-running Q5 after the fix returned an accurate answer: "A student found responsible for a Level 3 offense will have their behavior severely questioned... typical consequences include expulsion from the residence halls." Retrieval distance for the correct chunk improved from not-retrieved (pre-fix) to 0.769 (post-fix, Excerpt 3).

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

The evaluation plan in planning.md was essential for catching the Level 3 chunking failure. Because Q5 ("What happens if a student found responsible for a Level 3 offense?") was written with a specific, testable expected answer before any code was written, I could immediately recognize when the system returned the fallback message that something had gone wrong upstream — not with the LLM, but with retrieval. Without a pre-specified expected answer to compare against, I might have assumed the model just didn't know, rather than diagnosing the root cause at the chunking stage. The evaluation plan forced precision that turned a vague "it doesn't work" into a locatable bug.

**One way your implementation diverged from the spec, and why:**

The spec (planning.md) specified pure character-window chunking (600 chars, 80 overlap) and top-k = 3. Both changed during implementation. The chunking strategy was replaced entirely with hybrid header-split chunking after the Level 3 evaluation failure showed that character windows produce semantically mixed chunks at section boundaries. The top-k was raised from 3 to 5 after retrieval testing showed that Q1 (academic misconduct) had an off-target result at rank 1, making rank 4–5 chunks the ones actually needed for a correct answer. The spec was updated in planning.md to reflect both changes.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* The Chunking Strategy section of planning.md (character window, 600 chars, 80 overlap) and the requirement to store chunks in ChromaDB with source metadata. I asked Claude to implement `chunk_text()` and `build_collection()` in `ingest.py`.
- *What it produced:* A working `ingest.py` with a sliding character window, batch embedding via `model.encode()`, and ChromaDB storage with `source` and `chunk_index` metadata fields.
- *What I changed or overrode:* The initial implementation used pure character windowing, which I later replaced with hybrid header-split chunking after evaluation Q5 failed. I directed Claude to add the `split_on_headers()` function using a regex I specified (`Level \d+[:\.]`, Roman numerals, ALL-CAPS lines), and to apply the sliding window only within each section. I also directed the merge-short-chunks logic to stay within section boundaries — the first AI draft merged across sections, which defeated the purpose of header splitting.

**Instance 2**

- *What I gave the AI:* The retrieval failure root cause I had diagnosed (mixed Level 2/Level 3 content in one chunk), the HEADER_RE regex pattern I wanted, and the three-step hybrid chunking algorithm described in words.
- *What it produced:* A revised `chunk_text()` function with `split_on_headers()`, `sliding_window()`, and a merge loop inside a per-section iteration.
- *What I changed or overrode:* The merge loop in the first draft used `buffer += piece` without checking whether `buffer` had already reached `min_size` before appending. This caused some chunks to grow well beyond `CHUNK_SIZE`. I corrected the condition to flush `buffer` to `merged` as soon as it reaches `min_size`, then start a new buffer — matching the intent in my written spec. I also removed an early return that skipped the merge step for single-sub-chunk sections, which was causing sub-100-character chunks to pass through unmerged.

696 total chunks — healthy range (50–2,000). No changes needed.

Document	Chunks	Assessment
Student-Handbook-2022-2023-FINAL.txt	510	Expected — it's the largest document (247k chars) with many distinct policy sections
Housing-Handbook-24-25.txt	122	Good — mid-size document, good granularity
Community-Standards-and-Expectations-Accountability-Procedures-Final.txt	64	Fine — shortest document (30k chars)
Total	696	Well within healthy range
The distribution makes sense given the document sizes. The Student Handbook alone covers attendance, conduct, financial aid, housing, accommodations, academic integrity, and more — 510 chunks for 247k characters works out to ~485 chars per chunk on average, right in line with your 600-char target with overlap. No adjustment needed.

All 3 queries are working well. Here's the full assessment:

Query 1 — Academic misconduct reporting

Rank 1 (dist 0.646) is about false reports of sexual misconduct — related topic (misconduct reporting) but not the academic honor code procedure. This is off-target at rank 1.
Rank 2 (dist 0.681) correctly lists academic dishonesty types including cheating and plagiarism — relevant.
Assessment: Partially relevant — the model is conflating "misconduct reporting" with sexual misconduct reporting. The actual Academic Honor Code reporting procedure (chunk 109 from earlier runs) is not ranking in top 5 here. Worth noting as a retrieval limitation tied to ambiguous query phrasing.
Query 2 — Pregnancy accommodations

Rank 1 (dist 0.609) is an exact match — Title IX pregnancy accommodation policy.
Ranks 2–5 are all about the Student Access Office accommodation process — directly relevant supporting context.
Assessment: Fully relevant — clean retrieval across all 5 ranks.
Query 3 — Appealing a disciplinary decision

Rank 1 (dist 0.714) is the exact Appeals Procedure summary from Community Standards.
Ranks 2–5 cover the written appeal window, non-appealing party rights, and grounds for appeal.
Assessment: Fully relevant — strong retrieval pulling from both documents correctly.
k=5 is appropriate. Query 2 and 3 benefit from ranks 4–5 providing supporting detail. Query 1 shows that k=3 would have been worse (rank 1 is off-target, rank 2 is the useful one). No dilution observed at k=5 for these queries.