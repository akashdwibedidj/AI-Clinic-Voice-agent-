import chromadb
from sentence_transformers import SentenceTransformer
from loguru import logger

from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection


class RAGProcessor(FrameProcessor):
    """Intercepts user transcriptions, retrieves relevant chunks from
    the vector DB, and injects them into the LLM context before the
    LLM runs.
    """

    def __init__(self, context, db_path="./vector_db", collection_name="book_chunks", top_k=2):
        super().__init__()
        self.context = context
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.top_k = top_k

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # Only trigger RAG when we get a finalized user transcription
        if isinstance(frame, TranscriptionFrame) and frame.text.strip():
            query = frame.text.strip()
            logger.info(f"RAG: retrieving context for query: {query}")

            embed_q = self.embed_model.encode([query])
            results = self.collection.query(
                query_embeddings=[embed_q[0].tolist()],
                n_results=self.top_k,
            )

            chunks = results["documents"][0] if results["documents"] else []
            retrieved_context = "\n\n".join(chunks)

            if retrieved_context:
                # Inject retrieved context as a system-level message
                # right before this user turn gets processed by the LLM
                self.context.add_message(
                    {
                        "role": "system",
                        "content": (
                            "Use ONLY the following context to answer the "
                            f"user's next question if relevant:\n\n{retrieved_context}"
                        ),
                    }
                )
                logger.info(f"RAG: injected {len(chunks)} chunks into context")

        # Always pass the frame downstream unchanged
        await self.push_frame(frame, direction)