"""
Document cleaning pipeline.

Loads raw .txt files from documents/, cleans each one, saves cleaned
versions to documents/cleaned/, then prints a sample for manual review.

What is removed:
  - Lone page numbers (lines containing only a number, e.g. "5" or "Page 58")
  - PDF form-feed characters (\x0c)
  - Private-use Unicode bullets ( bullet,  link icon) → plain hyphen
  - Smart/curly hyphens and dashes (‐ ‑ ‒ – —) → plain ASCII hyphen or dash
  - Arrow characters (► ▶ →) used as decorative bullets → plain hyphen
  - Runs of 3+ blank lines collapsed to 2

What is kept:
  - All substantive policy text, section headers, numbered lists
  - URLs (they appear in contact/resource sections and are useful context)
  - Parenthetical revision dates like "(Adopted 1986; revised 2017)"
"""

import os
import re

RAW_DIR = "documents"
CLEAN_DIR = os.path.join(RAW_DIR, "cleaned")


def clean(text: str) -> str:
    # 1. Remove PDF page-break characters
    text = text.replace("\x0c", "\n")

    # 2. Remove lines that are only a page number ("5", "Page 58", "Page 88\n")
    text = re.sub(r"(?m)^\s*Page\s+\d+\s*$", "", text)
    text = re.sub(r"(?m)^\s*\d{1,3}\s*$", "", text)

    # 3. Replace private-use Unicode bullets with a plain hyphen-dash
    text = text.replace("", "-")   # filled bullet used in Student Handbook
    text = text.replace("", "-")   # link/globe icon used as a bullet

    # 4. Normalize smart hyphens and dashes to plain ASCII
    #    Non-breaking hyphen / figure dash / en-dash / em-dash → plain hyphen or dash
    text = text.replace("‐", "-")   # non-breaking hyphen
    text = text.replace("‑", "-")   # non-breaking hyphen variant
    text = text.replace("‒", "-")   # figure dash
    text = text.replace("–", "-")   # en-dash
    text = text.replace("—", " - ") # em-dash → spaced hyphen for readability
    text = text.replace("―", " - ") # horizontal bar

    # 5. Replace decorative arrow bullets with a plain hyphen
    text = re.sub(r"[►▶→]", "-", text)

    # 6. Remove PDF form-field placeholders left by unfilled template fields
    #text = re.sub(r"Click here to enter text\.?", "", text)

    # 7. Collapse runs of 3+ blank lines into exactly 2 (one blank line between sections)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 8. Strip trailing whitespace from every line
    text = "\n".join(line.rstrip() for line in text.splitlines())

    return text.strip()


def main():
    os.makedirs(CLEAN_DIR, exist_ok=True)

    for filename in sorted(os.listdir(RAW_DIR)):
        if not filename.endswith(".txt"):
            continue

        raw_path = os.path.join(RAW_DIR, filename)
        clean_path = os.path.join(CLEAN_DIR, filename)

        raw_text = open(raw_path, encoding="utf-8").read()
        cleaned_text = clean(raw_text)

        with open(clean_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        reduction = len(raw_text) - len(cleaned_text)
        print(f"{filename}")
        print(f"  Raw:     {len(raw_text):,} chars")
        print(f"  Cleaned: {len(cleaned_text):,} chars  (-{reduction:,} removed)")
        print()

    # Print 80 lines of the largest cleaned file for manual review
    largest = max(
        (f for f in os.listdir(CLEAN_DIR) if f.endswith(".txt")),
        key=lambda f: os.path.getsize(os.path.join(CLEAN_DIR, f)),
    )
    print("=" * 70)
    print(f"SAMPLE — first 80 lines of {largest}")
    print("=" * 70)
    lines = open(os.path.join(CLEAN_DIR, largest), encoding="utf-8").readlines()
    print("".join(lines[:80]))


if __name__ == "__main__":
    main()
