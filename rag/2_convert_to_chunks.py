import os
import json


def chunk_text(text, chunk_size=500, overlap=100):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = words[start:end]
        chunks.append(' '.join(chunk))
        start += chunk_size - overlap
    return chunks

os.makedirs('chunks', exist_ok=True)

# load already chunked books
already_chunked = set()
if os.path.exists('chunks/all_chunks.json'):
    with open('chunks/all_chunks.json', 'r') as f:
        all_chunks = json.load(f)
    already_chunked = set(chunk['book'] for chunk in all_chunks)
    print(f"Found {len(already_chunked)} already chunked — skipping")

all_chunks = []
if os.path.exists('chunks/all_chunks.json'):
    with open('chunks/all_chunks.json', 'r') as f:
        all_chunks = json.load(f)
new_books=0

for file in os.listdir('cleaned_texts'):
    if file.endswith('.txt'):
        if file in already_chunked:
            print(f"SKIP — {file}")
            continue

        with open(os.path.join('cleaned_texts', file), 'r', encoding='utf-8') as f:
            text = f.read()
        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "book": file,
                "chunk_id": i,
                "text": chunk
            })
            
        print(f"New - {file} - {len(chunks)} chunks created")
        new_books += 1


with open('chunks/all_chunks.json', 'w', encoding='utf-8') as f:
    json.dump(all_chunks, f, indent=2)

print(f"\nDone! {new_books} new books added")
print(f'\nDone! Total chunks: {len(all_chunks)}')