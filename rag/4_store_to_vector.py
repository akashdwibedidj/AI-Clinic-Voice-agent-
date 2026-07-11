import json
import numpy as np
import chromadb


embeddings =np.load('chunks/embeddings.npy')
with open('chunks/all_chunks.json', 'r', encoding='utf-8') as f:
    all_chunks = json.load(f)
print(f"Loaded {len(all_chunks)} chunks")


client = chromadb.PersistentClient(path='vector_db/')
collection = client.get_or_create_collection(name='book_chunks')


old_count = collection.count()
print(f"ChromaDB already has{old_count} chunks")

new_chunks = all_chunks[old_count:]
new_embeddings = embeddings[old_count:]

if len(new_chunks) == 0:
    print("Nothing new to insert!")
else:
    batch_size = 500
    for i in range(0, len(new_chunks), batch_size):
        batch = new_chunks[i:i+batch_size]
        batch_emb = new_embeddings[i:i+batch_size]

        ids   = [f"{item['chunk_id']}_{item['book']}" for item in batch]
        docs  = [item['text'] for item in batch]
        metas = [{'book': item['book'], 'chunk_id':item['chunk_id']} for item in batch]
        embs  = batch_emb.tolist()

        collection.add(
            ids=ids,
            embeddings=embs,
            documents=docs,
            metadatas=metas
        )

        print(f"Inserted {min(i+batch_size, len(new_chunks))}/{len(new_chunks)}")
    print(f"\nDone! {len(new_chunks)} chunks stored in ChromaDB")
    print(f"Total in ChromaDB now: {collection.count()}")

