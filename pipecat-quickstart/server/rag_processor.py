import re
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

        # NEW: remember index of the last RAG-injected message so we can replace it
        self._last_rag_msg = None

        # NEW: simple booking-intent detector to skip retrieval once slot-filling starts
        self._booking_pattern = re.compile(
            r"\b(book|appointment|confirm|yes|schedule|\d{1,2}\s?(am|pm)|"
            r"january|february|march|april|may|june|july|august|september|october|november|december)\b",
            re.IGNORECASE,
        )

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame) and frame.text.strip():
            query = frame.text.strip()

            # NEW: skip retrieval once the user seems to be confirming/booking
            # (short utterances like "Yes.", "At one PM.", dates, etc.)
            if self._booking_pattern.search(query) or len(query.split()) <= 4:
                logger.info(f"RAG: skipping retrieval, booking-intent detected: {query}")
                await self.push_frame(frame, direction)
                return

            logger.info(f"RAG: retrieving context for query: {query}")

            embed_q = self.embed_model.encode([query])
            results = self.collection.query(
                query_embeddings=[embed_q[0].tolist()],
                n_results=self.top_k,
            )

            chunks = results["documents"][0] if results["documents"] else []
            retrieved_context = "\n\n".join(chunks)

            if retrieved_context:
                new_msg = {
                    "role": "system",
                    "content": (
                        "Use ONLY the following context to answer the "
                        f"user's next question if relevant:\n\n{retrieved_context}"
                    ),
                }

                # NEW: replace the previous RAG message instead of appending a new one
                if self._last_rag_msg is not None and self._last_rag_msg in self.context.messages:
                    idx = self.context.messages.index(self._last_rag_msg)
                    self.context.messages[idx] = new_msg
                else:
                    self.context.add_message(new_msg)

                self._last_rag_msg = new_msg
                logger.info(f"RAG: injected {len(chunks)} chunks into context (replaced old injection)")

        await self.push_frame(frame, direction)