# PolicyAI

PolicyAI is a document intelligence and retrieval-augmented generation (RAG) application for policy and regulatory documents. It converts uploaded PDFs into structured, searchable knowledge and answers user questions using retrieved evidence with source citations.

The project was built to demonstrate production-oriented RAG engineering rather than a basic “chat with PDF” workflow.

## Features

- PDF upload and structured extraction with Docling
- Markdown and structured JSON export
- Section-aware chunking
- Dense embeddings using BGE-M3
- Sparse BM25 retrieval
- Qdrant hybrid search with reciprocal rank fusion
- Cross-encoder reranking
- Grounded answer generation using Qwen through Ollama
- Source citations with document, section, and page metadata
- Refusal when retrieved evidence is insufficient
- Document-specific search
- Document listing and deletion
- Multi-turn follow-up questions using lightweight session history
- FastAPI API and HTMX interface
- Automated evaluation for retrieval, citations, refusals, response length, and answer completeness

## Tech Stack

- **Backend:** FastAPI
- **UI:** Jinja2 + HTMX
- **PDF processing:** Docling
- **Dense embeddings:** BAAI/bge-m3
- **Sparse retrieval:** Qdrant BM25 through FastEmbed
- **Vector database:** Qdrant
- **Reranker:** BAAI/bge-reranker-v2-m3
- **LLM:** Qwen 3 via Ollama
- **Package management:** uv
- **Language:** Python 3.12

## Architecture

```text
PDF Upload
    ↓
Docling Extraction
    ↓
Structured Markdown + JSON
    ↓
Document Parsing
    ↓
Metadata Enrichment
    ↓
Section-Aware Chunking
    ↓
Dense + Sparse Embeddings
    ↓
Qdrant Hybrid Index
    ↓
Hybrid Retrieval + Reranking
    ↓
Grounded Generation
    ↓
FastAPI + HTMX UI
```

See [docs/architecture.md](docs/architecture.md) for more detail.

## Evaluation Summary

The current evaluation contains 15 questions drawn from the indexed procurement regulations, including two unsupported questions.

| Metric                             |        Result |
| ---------------------------------- | ------------: |
| Top-1 retrieval accuracy           |          100% |
| Top-5 retrieval accuracy           |          100% |
| Citation rate                      |          100% |
| Unsupported-query refusal accuracy |          100% |
| Word-limit compliance              |          100% |
| Answer completeness                |         84.6% |
| Average response time              | 10.96 seconds |
| Average answer length              |      66 words |

These results are encouraging but should be interpreted as MVP benchmarks because the dataset and test set are still small.

See [docs/evaluation.md](docs/evaluation.md) for details.

## Project Structure

```text
src/policy_ai/
├── api/
│   └── main.py
├── evaluation/
│   └── evaluator.py
├── generation/
│   ├── generator.py
│   └── query_rewriter.py
├── ingestion/
│   ├── converter.py
│   ├── parser.py
│   ├── metadata.py
│   ├── chunker.py
│   ├── embedder.py
│   └── pipeline.py
├── knowledge/
│   └── indexer.py
├── retrieval/
│   └── retriever.py
├── static/
│   └── styles.css
└── templates/
    ├── base.html
    ├── index.html
    └── partials/
```

## Local Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Start Qdrant

```bash
docker run -d \
  --name policy-ai-qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v policy_ai_qdrant:/qdrant/storage \
  qdrant/qdrant
```

### 3. Install and start Ollama

Pull the model:

```bash
ollama pull qwen3:8b
```

Ensure Ollama is running before starting the application.

### 4. Run the application

```bash
uv run uvicorn policy_ai.api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## Main API Endpoints

### Ask a question

```http
POST /ask
```

```json
{
  "question": "What are the requirements for open tendering?",
  "limit": 5,
  "filename": "ppadr.pdf"
}
```

### Upload a document

```http
POST /documents
```

### List documents

```http
GET /documents
```

### Delete a document

```http
DELETE /documents/{filename}
```

## Example Use Cases

- Regulatory question answering
- Public policy research
- Procurement compliance assistance
- Internal knowledge assistants
- Document search across policy collections
- Exact and semantic retrieval from legal or technical documents

## Current Limitations

- Regulation-aware chunking is not yet implemented
- Document amendment and supersession tracking are not included
- The current evaluation uses one main regulation document and a small test set
- Extracted tables may require additional validation
- Data is stored in files and Qdrant rather than PostgreSQL
- Authentication and role-based access are not included
- The application currently runs local models through Ollama

See [docs/limitations.md](docs/limitations.md) for the full list.

## Portfolio Positioning

This project demonstrates:

- production-oriented RAG architecture
- hybrid information retrieval
- reranking and source filtering
- document ingestion and indexing pipelines
- grounded LLM generation
- API and interface development
- automated evaluation of retrieval and generation quality

## License

This project is licensed under the [MIT License](LICENSE).
