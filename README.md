# PolicyAI

PolicyAI is a retrieval-augmented generation application for policy, legal, and regulatory documents. Users can upload PDFs, search them with natural-language questions, and receive grounded answers with source citations.

## Features

- User registration and login
- JWT authentication and role-based access
- User-owned document collections
- PDF extraction with Docling
- Regulation-aware chunking
- Dense and sparse hybrid retrieval
- Qdrant vector search with reranking
- Neighbouring-chunk context expansion
- Grounded answers with citations
- React frontend and FastAPI backend
- Automated retrieval and answer evaluation

## Tech Stack

- FastAPI
- React and Vite
- SQLAlchemy and Alembic
- SQLite
- Docling
- BGE-M3
- Qdrant BM25
- BGE Reranker v2 M3
- Qwen 3 through Ollama
- Python 3.12
- uv

## Architecture

```text
React UI
   ↓
FastAPI
   ↓
Authentication and authorization
   ↓
PDF ingestion and chunking
   ↓
Dense and sparse embeddings
   ↓
Qdrant hybrid retrieval
   ↓
Reranking and neighbour expansion
   ↓
Grounded answer with citations
```

## Evaluation

Current MVP results:

| Metric                   | Result |
| ------------------------ | -----: |
| Top-1 retrieval accuracy |   100% |
| Top-5 retrieval accuracy |   100% |
| Citation rate            |   100% |
| Refusal accuracy         |   100% |
| Word-limit compliance    |   100% |
| Answer completeness      |  92.3% |

## Local Setup

### Backend

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn policy_ai.api.main:app --reload
```

### Qdrant

```bash
docker run -d \
  --name policy-ai-qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v policy_ai_qdrant:/qdrant/storage \
  qdrant/qdrant
```

### Ollama

```bash
ollama pull qwen3:8b
ollama serve
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Backend `.env`:

```env
DATABASE_URL=
SECRET_KEY=
QDRANT_URL=
COLLECTION_NAME=
FRONTEND_URL=
```

Frontend `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Main Endpoints

```text
POST   /auth/register
POST   /auth/login
GET    /auth/me
POST   /documents
GET    /documents
DELETE /documents/{document_id}
POST   /ask
```

## License

MIT
