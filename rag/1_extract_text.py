import fitz  # pymupdf
# import ebooklib
# from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re

# ── paths ──────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR      = os.path.join(BASE_DIR, "books")
OUTPUT_DIR     = os.path.join(BASE_DIR, "cleaned_texts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── helpers ────────────────────────────────────────────────────────────────
def clean_text(text):
    """Remove noise that appears in most books."""
    text = re.sub(r'\n{3,}', '\n\n', text)        # collapse blank lines
    text = re.sub(r'[ \t]{2,}', ' ', text)         # collapse spaces
    text = re.sub(r'\b\d+\b\n', '', text)           # remove lone page numbers
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)     # remove non-ASCII garbage
    text = text.strip()
    return text

def extract_pdf(filepath):
    """Extract text from a PDF file using PyMuPDF."""
    doc = fitz.open(filepath)
    full_text = []
    for page in doc:
        full_text.append(page.get_text())
    doc.close()
    return "\n".join(full_text)

def extract_epub(filepath):
    """Extract text from an EPUB file."""
    book = epub.read_epub(filepath)
    full_text = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            full_text.append(soup.get_text(separator='\n'))
    return "\n".join(full_text)

# ── main loop ──────────────────────────────────────────────────────────────
def process_all_books():
    books = os.listdir(BOOKS_DIR)
    total = len(books)
    success = 0
    failed = []

    print(f"\n Found {total} files in books/ folder")
    print(f" Starting extraction...\n")
    print("-" * 50)

    for i, filename in enumerate(books, 1):
        filepath = os.path.join(BOOKS_DIR, filename)
        name     = os.path.splitext(filename)[0]   # filename without extension
        ext      = os.path.splitext(filename)[1].lower()
        out_path = os.path.join(OUTPUT_DIR, name + ".txt")

        # skip if already processed
        if os.path.exists(out_path):
            print(f"[{i}/{total}] SKIP (already done) — {filename}")
            success += 1
            continue

        try:
            if ext == ".pdf":
                raw_text = extract_pdf(filepath)
            elif ext == ".epub":
                raw_text = extract_epub(filepath)
            elif ext == ".txt":
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_text = f.read()
            else:
                print(f"[{i}/{total}] SKIP (unsupported format) — {filename}")
                continue

            cleaned = clean_text(raw_text)

            # only save if we actually got text
            if len(cleaned) < 100:
                print(f"[{i}/{total}] WARN (too short, might be scanned) — {filename}")
                failed.append(filename)
                continue

            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(cleaned)

            size_kb = len(cleaned) // 1024
            print(f"[{i}/{total}] OK  ({size_kb} KB extracted) — {filename}")
            success += 1

        except Exception as e:
            print(f"[{i}/{total}] FAIL — {filename}  |  Error: {e}")
            failed.append(filename)

    # ── summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print(f" DONE")
    print(f" Successful : {success}")
    print(f" Failed     : {len(failed)}")
    if failed:
        print(f"\n Books that failed:")
        for f in failed:
            print(f"   - {f}")
    print("=" * 50)
    print(f"\n Cleaned text files saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_all_books()