# AI Clinic Voice Agent

A real-time voice agent for a private hospital that understands patient queries, retrieves doctor information using RAG, and books appointments directly to Google Calendar via an n8n automation workflow.

I used local llm like mistral 7b/llama3.1 for better use claude/chatgpt api's

Built with [Pipecat](https://github.com/pipecat-ai/pipecat) — Speech-to-Text → RAG → LLM (with function calling) → Text-to-Speech.

---

## Features

- 📒 Full RAG processing takes pdf docs stores in vectordb more then 1 milion pages store capacity
- 🎙️ Real-time voice conversation (WebRTC)
- 📚 RAG-powered doctor information retrieval (ChromaDB + Sentence Transformers)
- 🗓️ Automatic appointment booking to Google Calendar via n8n
- 🧠 Local LLM support via Ollama (function-calling enabled)
- 🔊 Configurable STT/TTS providers (Deepgram, Cartesia)

---

## RAG-Pipeline

run rag_pipeline.py
it will run the full pipeline of extraction and storing doctor data in chromadb.
store your pdf's in doc_data/ and the pipeline will do all your work keep the doc name what with the doctor name since it will be chunk name.


## How does it work?
```
PDF → Extract Text → Chunk → Embed → ChromaDB
                                              ↓
User Question → Embed → Search ChromaDB → Top 2 Chunks
                                              ↓
                                         Mistral 7B/ llama3.1
                                              ↓
                                       Answer + Source
```
1. Books are extracted, cleaned and split into 500-word overlapping chunks
2. Each chunk is converted into a 384-dimension vector using 
   sentence-transformers
3. Vectors are stored in ChromaDB for semantic search
4. When you ask a question, it is embedded and matched against all chunks
5. Top 2 most relevant chunks are sent to Mistral 7B/llama3.1 via Ollama
6. Mistral reads only those chunks and generates a precise answer

## Pipecat

run bot.py in pipecat-quickstart/server/
it totally triggers all the functions needs for calling stt, tts, rag, agent etc.

! to store new data files use rag_pipeline.py but to call the agent use bot.py

## Pipecat Architecture

```
User speech
    │
    ▼
Deepgram STT  ──────► transcribes audio to text
    │
    ▼
RAGProcessor  ──────► retrieves relevant doctor info from ChromaDB
    │                 and injects it into LLM context
    ▼
OpenAI-compatible LLM (Ollama) ──► decides response / triggers
    │                              book_appointment tool
    ▼
book_appointment_tool() ──► POSTs to n8n webhook
    │
    ▼
n8n Workflow ──────► Google Calendar (creates event)
    │
    ▼
Cartesia TTS ──────► converts LLM response to speech
    │
    ▼
User hears response
```

---

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- [Ollama](https://ollama.com/) installed locally
- [n8n](https://n8n.io/) running locally (self-hosted or Docker)
- API keys:
  - Deepgram (STT)
  - Cartesia (TTS)
- Google account connected to n8n (OAuth2, configured inside n8n itself)

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd pipecat-quickstart/server
uv sync
```

### 2. Pull a tool-calling capable LLM via Ollama

> ⚠️ Not all local models support function calling reliably. `mistral:latest` does **not** — use one of the following instead:

```bash
ollama pull llama3.1:8b
# or
ollama pull qwen2.5:7b-instruct
```

Verify the exact tag with:

```bash
ollama list
```

### 3. Configure environment variables

Create a `.env` file in the `server/` directory:

```env
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key
CARTESIA_VOICE_ID=71a7ad14-091c-4e8e-a314-022ece01c121

OPENAI_API_KEY=ollama          # placeholder, Ollama doesn't require a real key
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:8b
```

### 4. Set up the vector database

Doctor information (from your source PDF/document) must be chunked and embedded into ChromaDB at the path referenced by `VECTOR_DB_PATH` in `bot.py` (defaults to `../../vector_db`). Use `all-MiniLM-L6-v2` embeddings to match `RAGProcessor`.

### 5. Set up n8n

1. Start n8n locally (default: `http://localhost:5678`)
2. Create a workflow with:
   - **Webhook** node → set path to `/create-event`, method `POST`
   - **Google Calendar** node → **Create Event**, connected via OAuth2 credential
   - Map `{{$json.body.title}}`, `{{$json.body.start}}`, `{{$json.body.end}}` into the Calendar node's fields
3. Activate the workflow (toggle top-right)
4. Confirm the webhook URL matches `N8N_WEBHOOK_URL` in `bot.py`:

```python
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/create-event"
```

### 6. Run the bot

```bash
uv run bot.py
```

Open `http://localhost:7860` in your browser to start a voice session.

---

## Project Structure

```
server/
├── bot.py              # Main pipeline: STT → RAG → LLM → TTS, tool registration
├── rag_processor.py     # Custom FrameProcessor for retrieval-augmented context injection
├── n8n_test.py          # Standalone script to test the n8n webhook directly
├── .env                 # API keys and config (not committed)
└── vector_db/            # ChromaDB persistent storage (doctor knowledge base)
```

---

## How Appointment Booking Works

1. User confirms a purpose, date, and time in conversation.
2. The LLM (via native function calling) invokes `book_appointment` with `title`, `start`, and `end` (ISO 8601).
3. `book_appointment_tool()` in `bot.py` sends this payload to the n8n webhook.
4. n8n's Google Calendar node creates the event using the connected Google account.
5. The agent confirms the booking back to the user via voice.

> **Note:** Tool calling requires an LLM checkpoint specifically trained for structured function calling. Base/instruct models without this training (e.g. plain `mistral`) will describe the booking in text instead of actually triggering it — always verify with `qwen2.5` or `llama3.1` class models.

---

## Testing the Webhook Independently

Use `n8n_test.py` to confirm the n8n → Google Calendar path works before testing through voice:

```bash
python n8n_test.py
```

Expected output: HTTP 200 with a JSON response containing the created event's `id`, `htmlLink`, and `status: confirmed`.

---

## Known Issues / Gotchas

- **RAG context bloat**: The `RAGProcessor` must **replace** its last injected system message rather than appending a new one each turn — otherwise the context window fills with duplicate content and degrades LLM output quality.
- **Timezone mismatches**: Ensure the Google Calendar node's timezone setting in n8n matches your actual locale (e.g. `Asia/Kolkata`), or explicitly send UTC timestamps from the agent.
- **HTTP 402 errors**: Indicates STT/TTS provider credits are exhausted — check Deepgram/Cartesia billing dashboards.
- **Local LLM tool calling**: Confirm your chosen Ollama model actually supports function calling before debugging the rest of the pipeline.

---

## License

BSD 2-Clause License — see individual file headers for details.