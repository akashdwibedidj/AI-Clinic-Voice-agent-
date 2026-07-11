from sentence_transformers import SentenceTransformer
import json
import numpy as np


model = SentenceTransformer('all-MiniLM-L6-v2')

with open('chunks/all_chunks.json', 'r', encoding='utf-8') as f:
    all_chunks = json.load(f)

old_embeddings = np.load('chunks/embeddings.npy')
old_count = len(old_embeddings)

print(f"Existing embeddings: {old_count}")
print(f"Total chunks now: {len(all_chunks)}")

new_chunks = all_chunks[old_count:]
print(f"New chunks to embed: {len(new_chunks)}")
if len(new_chunks) ==0:
    print("No new chunks to embed!")
else:

    texts = [item['text'] for item in new_chunks]

    new_embeddings = model.encode(texts, show_progress_bar=True)
    all_embeddings = np.vstack([old_embeddings, new_embeddings])

    # embeddings is already a numpy array → no need for np.array()
    np.save('chunks/embeddings.npy', all_embeddings)
    print(f"\nDone!")
    print(f"Old count: {old_count}")
    print(f"New count: {len(new_chunks)}")
    print(f"Total embeddings: {len(all_embeddings)}")
    print(f"Shape: {all_embeddings.shape}")