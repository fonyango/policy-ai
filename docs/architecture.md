# PolicyAI Architecture

## Overview

PolicyAI is a modular RAG system for policy, legal, and regulatory documents. Each stage is inspectable so errors can be traced from the final answer back to the original PDF.

## Flow

```text
Authenticated User
    ↓
React UI
    ↓
FastAPI
    ↓
Authorization Check
    ↓
PDF Ingestion with Docling
    ↓
Parsing and Metadata Enrichment
    ↓
Regulation-Aware Chunking
    ↓
Dense and Sparse Embeddings
    ↓
Qdrant Hybrid Retrieval
    ↓
Cross-Encoder Reranking
    ↓
Neighbouring-Chunk Expansion
    ↓
Qwen Grounded Generation
    ↓
Answer with Citations
```

## Main Components

### Ingestion

Validates PDFs, stores the source file, and converts documents into Markdown and structured JSON.

```text
src/policy_ai/ingestion/
```

### Chunking

Preserves section and regulation boundaries, filters table-of-contents chunks, and splits oversized content safely.

```text
src/policy_ai/ingestion/chunker.py
```

### Indexing

Stores dense vectors, sparse BM25 vectors, document metadata, ownership data, page ranges, and chunk content in Qdrant.

```text
src/policy_ai/knowledge/indexer.py
```

### Retrieval

Combines dense and sparse search, reciprocal rank fusion, reranking, ownership filters, document filters, and neighbouring-chunk expansion.

```text
src/policy_ai/retrieval/retriever.py
```

### Generation

Uses only retrieved evidence, cites factual claims, keeps answers concise, and refuses unsupported questions.

```text
src/policy_ai/generation/generator.py
```

### Authentication and Authorization

FastAPI manages JWT authentication, user roles, document ownership, and protected endpoints.

```text
src/policy_ai/auth/
```

### Interface

React provides authentication, document upload, document selection, question answering, citations, and admin-only deletion controls.

```text
frontend/src/
```

## Design Principles

- **Inspectability:** Every pipeline stage can be reviewed independently.
- **Modularity:** Models and storage components can be replaced separately.
- **Precision first:** Dense and lexical retrieval are combined.
- **Grounding:** Retrieved documents remain the source of truth.
- **Authorization:** Users can access only permitted documents.
- **Refusal over guessing:** Weak evidence produces an explicit refusal.
