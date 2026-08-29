# DocuQuery — AI Document Intelligence Platform

Upload PDFs, ask questions, get grounded answers with exact source citations (document name + page number + chunk text). Built to demonstrate real RAG engineering: proper chunking, local embeddings, FAISS vector search, and a swappable LLM layer — not just an API wrapper.

---

## Architecture

```
                React (Vite)
                     │
                     ▼
                 FastAPI
                     │
           ┌─────────┴─────────┐
           ▼                   ▼
    Document Processing    Query API
           │                   │
           ▼                   ▼
       Chunking            Embeddings
    (sentence-boundary   (sentence-transformers
     500-tok window,       all-MiniLM-L6-v2)
     50-tok overlap)           │
           │                   │
           └─────────┬─────────┘
                     ▼
              FAISS (local)
              + JSON sidecar
                     │
                     ▼
                    RAG
              (grounded prompt
               + deduplication)
                     │
                     ▼
                    LLM
              (Groq — default, free)
              (OpenAI / Ollama /
               Hugging Face)
                     │
                     ▼
           Streaming Answer + Source Citations
           (doc name, page, chunk text)
           via Server-Sent Events (SSE)
```

Two distinct flows through the same FastAPI service:

**Ingestion:** `POST /api/v1/documents` → PDF extraction (pypdf, per-page) → sentence-boundary chunking → sentence-transformers embeddings → FAISS index + Postgres chunk records

**Query:** `POST /api/v1/query/ask/stream` → embed question (LRU cached) → FAISS top-k search → deduplicate chunks → assemble grounded prompt → Groq LLM → stream tokens via SSE → answer + source citations persisted to conversation history

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Database | PostgreSQL on **Neon** (free tier), SQLAlchemy 2, Alembic |
| Vector store | FAISS (local, CPU) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, no API key) |
| LLM | **Groq** (default, free API) / OpenAI / Ollama / Hugging Face |
| Streaming | Server-Sent Events (SSE) — token-by-token streaming |
| Frontend | React 18, Vite, React Router, Axios |
| Tests | pytest, httpx |

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Free [Groq API key](https://console.groq.com) (default LLM — takes 30 seconds to get)

### 1. Clone & configure

```bash
git clone https://github.com/vigneshsai4202/DocQuery.git
cd DocQuery
```

### 2. Create a free Neon database

1. Go to [neon.tech](https://neon.tech) and create a free project.
2. In the Neon dashboard → **Connection Details**, copy the **psycopg2** connection string:
   ```
   postgresql+psycopg2://user:password@ep-xxx-yyy.region.aws.neon.tech/dbname?sslmode=require
   ```
3. Paste it as `DATABASE_URL` in your `.env`.

### 3. Backend

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — set DATABASE_URL and OPENAI_API_KEY (your Groq key)
```

Run Alembic migrations (creates all tables on Neon):

```bash
alembic upgrade head
```

Start the API server:

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

### 4. Frontend

```bash
cd ../frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## Running Tests

```bash
cd backend
pytest
# With coverage:
pytest --cov=app --cov-report=term-missing
```

Test coverage includes:
- Chunking logic (sentence-boundary, overlap, multi-page, edge cases)
- System user auto-creation (single-user mode)
- Document upload (happy path, wrong extension, size limit, delete)
- Embedding/vector store pipeline (add, search, delete-by-document)
- Query/RAG endpoints (conversation creation, append, streaming)

---

## LLM Provider

### Groq (default — free, fast)

Get a free API key at [console.groq.com](https://console.groq.com) → API Keys → Create.

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=gsk_...          # your Groq key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
```

Groq uses the OpenAI-compatible API format, so `LLM_PROVIDER=openai` is correct.

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### Ollama (local, no API key)

```bash
# Install from https://ollama.com, then:
ollama pull llama3.2
```

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Hugging Face Inference API

```env
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=hf_...
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-3B-Instruct
```

---

## Embedding Provider

```env
# Local (default — no API key, ~90 MB model download on first run):
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# OpenAI:
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

> **Important:** if you change the embedding model after documents are already indexed, delete `backend/storage/vector_store/` and re-upload your documents. Vectors from different models are not compatible.

---

## API Reference

Full interactive docs at `/docs` (Swagger UI) and `/redoc`.

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/documents` | Upload PDF (multipart) |
| GET | `/api/v1/documents` | List documents |
| GET | `/api/v1/documents/{id}` | Get document + status |
| DELETE | `/api/v1/documents/{id}` | Delete doc + vectors |
| POST | `/api/v1/query/ask` | RAG query → full answer + sources |
| POST | `/api/v1/query/ask/stream` | RAG query → streaming SSE response |
| POST | `/api/v1/query/search` | Semantic search only (no LLM) |
| GET | `/api/v1/conversations` | List conversations |
| GET | `/api/v1/conversations/{id}` | Full conversation with messages |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation |

---

## Project Structure

```
DocQuery/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app, CORS, router registration
│   │   ├── api/
│   │   │   ├── documents.py          # upload, list, delete
│   │   │   ├── query.py              # /ask, /ask/stream (SSE), /search
│   │   │   └── conversations.py      # history CRUD
│   │   ├── core/
│   │   │   ├── config.py             # pydantic-settings, all env vars
│   │   │   └── security.py           # single system user (no login required)
│   │   ├── models/
│   │   │   ├── orm.py                # SQLAlchemy: User, Document, Chunk, Conversation, Message
│   │   │   └── schemas.py            # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── chunking.py           # sentence-boundary sliding window chunker
│   │   │   ├── embeddings.py         # BaseEmbedder → LocalEmbedder / OpenAIEmbedder
│   │   │   ├── vector_store.py       # FAISS wrapper + JSON metadata sidecar
│   │   │   ├── llm_provider.py       # BaseLLMProvider → Groq / OpenAI / Ollama / HuggingFace
│   │   │   ├── document_processor.py # ingestion pipeline (extract → chunk → embed → store)
│   │   │   └── rag.py                # retrieve, deduplicate, cache, stream, answer
│   │   └── db/
│   │       ├── base.py               # engine, SessionLocal, Base, get_db
│   │       └── migrations/           # Alembic env.py + initial schema
│   ├── tests/                        # 22 pytest tests
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
├── frontend/
│   └── src/
│       ├── api.js                    # axios instance
│       ├── App.jsx                   # routes
│       ├── components/
│       │   └── Layout.jsx            # sidebar nav
│       └── pages/
│           ├── ChatPage.jsx          # streaming chat with source citations
│           ├── DocumentsPage.jsx     # upload + status polling
│           └── HistoryPage.jsx       # conversation history
└── README.md
```
