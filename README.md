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
    (500-tok window,    (sentence-transformers
     50-tok overlap)      or OpenAI)
           │                   │
           └─────────┬─────────┘
                     ▼
              FAISS (local)
              + JSON sidecar
                     │
                     ▼
                    RAG
              (grounded prompt)
                     │
                     ▼
                    LLM
              (Ollama / OpenAI /
               Hugging Face)
                     │
                     ▼
           Answer + Source Citations
           (doc name, page, chunk text)
```

Two distinct flows through the same FastAPI service:

**Ingestion:** `POST /api/v1/documents` → PDF extraction (pypdf, per-page) → sliding-window chunking → sentence-transformers embeddings → FAISS index + Postgres chunk records

**Query:** `POST /api/v1/query/ask` → embed question → FAISS top-k search → assemble grounded prompt → LLM → answer + source chunks returned and persisted to conversation history

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Database | PostgreSQL on **Neon** (free tier), SQLAlchemy 2, Alembic |
| Vector store | FAISS (local, CPU) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (default, local) |
| LLM | Ollama (default, local) / OpenAI / Hugging Face |
| Auth | JWT (PyJWT + bcrypt) |
| Frontend | React 18, Vite, React Router, Axios |
| Tests | pytest, httpx |

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) (for the default LLM — or swap to OpenAI/HuggingFace)

### 1. Clone & configure

```bash
git clone <repo-url>
cd DocQuery
```

### 2. Create a free Neon database

1. Go to [neon.tech](https://neon.tech) and create a free project.
2. In the Neon dashboard → **Connection Details**, copy the **psycopg2** connection string. It looks like:
   ```
   postgresql+psycopg2://user:password@ep-xxx-yyy.region.aws.neon.tech/dbname?sslmode=require
   ```
3. Paste it as `DATABASE_URL` in your `.env` (see next step).

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
# Edit .env — at minimum set DATABASE_URL and JWT_SECRET_KEY
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

### 4. LLM — Ollama (default)

```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.2
# Ollama runs automatically on http://localhost:11434
```

### 5. Frontend

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
- Chunking logic (overlap, multi-page, edge cases)
- Auth endpoints (signup, login, duplicate email, bad credentials)
- Document upload (happy path, wrong extension, size limit, delete)
- Embedding/vector store pipeline (add, search, delete-by-document)
- Query/RAG endpoints (conversation creation, append, unauthenticated)

---

## Swapping the LLM Provider

Set `LLM_PROVIDER` in `.env`:

### Ollama (default — free, local)
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```
Pull any model: `ollama pull mistral`, `ollama pull phi3`, etc.

### OpenAI (or any OpenAI-compatible API)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
# For Azure OpenAI or local vLLM, change OPENAI_BASE_URL:
# OPENAI_BASE_URL=https://your-endpoint/openai/deployments/your-model
```

### Hugging Face Inference API
```env
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=hf_...
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-3B-Instruct
```

---

## Swapping the Embedding Provider

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

> **Important:** if you change the embedding model after documents are already indexed, delete the FAISS index files (`backend/storage/vector_store/`) and re-upload your documents. Vectors from different models are not compatible.

---

## API Reference

Full interactive docs at `/docs` (Swagger UI) and `/redoc`.

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/signup` | Create account, returns JWT |
| POST | `/api/v1/auth/login` | Login, returns JWT |
| GET | `/api/v1/auth/me` | Current user info |
| POST | `/api/v1/documents` | Upload PDF (multipart) |
| GET | `/api/v1/documents` | List user's documents |
| GET | `/api/v1/documents/{id}` | Get document + status |
| DELETE | `/api/v1/documents/{id}` | Delete doc + vectors |
| POST | `/api/v1/query/ask` | RAG query → answer + sources |
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
│   │   ├── main.py                  # FastAPI app, CORS, router registration
│   │   ├── api/
│   │   │   ├── auth.py              # signup, login, /me
│   │   │   ├── documents.py         # upload, list, delete
│   │   │   ├── query.py             # /ask (RAG), /search (retrieval only)
│   │   │   └── conversations.py     # history CRUD
│   │   ├── core/
│   │   │   ├── config.py            # pydantic-settings, all env vars
│   │   │   └── security.py          # JWT, bcrypt
│   │   ├── models/
│   │   │   ├── orm.py               # SQLAlchemy models
│   │   │   └── schemas.py           # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── chunking.py          # sliding-window token-approximate chunker
│   │   │   ├── embeddings.py        # BaseEmbedder, LocalEmbedder, OpenAIEmbedder
│   │   │   ├── vector_store.py      # FAISS wrapper + JSON metadata sidecar
│   │   │   ├── llm_provider.py      # BaseLLMProvider, Ollama/OpenAI/HuggingFace
│   │   │   ├── document_processor.py# ingestion pipeline (extract→chunk→embed→store)
│   │   │   └── rag.py               # retrieve_chunks + answer_question
│   │   └── db/
│   │       ├── base.py              # engine, SessionLocal, Base, get_db
│   │       └── migrations/          # Alembic env.py + versions/
│   ├── tests/
│   │   ├── conftest.py              # SQLite in-memory fixtures, TestClient
│   │   ├── test_chunking.py
│   │   ├── test_auth.py
│   │   ├── test_documents.py
│   │   ├── test_embeddings.py
│   │   └── test_query.py
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api.js                   # axios instance with auth interceptor
│   │   ├── App.jsx                  # routes
│   │   ├── context/AuthContext.jsx  # login/signup/logout state
│   │   ├── components/
│   │   │   ├── Layout.jsx           # sidebar nav
│   │   │   └── ProtectedRoute.jsx
│   │   └── pages/
│   │       ├── AuthPage.jsx         # login + signup
│   │       ├── DocumentsPage.jsx    # upload + list + status polling
│   │       ├── ChatPage.jsx         # RAG chat with source citations
│   │       └── HistoryPage.jsx      # conversation history
│   └── vite.config.js
└── README.md
```
