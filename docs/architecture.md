# PolicyAI Architecture

## Overview

PolicyAI is designed as a modular document intelligence pipeline. Each stage has one responsibility and produces inspectable output. This makes retrieval failures traceable from the final answer back to the original PDF.

## High-Level Flow

```text
User Upload
    ↓
FastAPI Upload Endpoint
    ↓
PDF saved to data/raw/
    ↓
Docling Conversion
    ├── Markdown
    └── Structured JSON
    ↓
Parser
    ↓
Metadata Enrichment
    ↓
Section-Aware Chunking
    ↓
Dense Embedding Generation
    ↓
Sparse BM25 Representation
    ↓
Qdrant Index
    ↓
Hybrid Retrieval
    ↓
Cross-Encoder Reranking
    ↓
Evidence Filtering
    ↓
Qwen Grounded Generation
    ↓
FastAPI JSON or HTMX Response
```

## Components

### 1. Ingestion

The ingestion layer accepts policy or regulatory PDFs and converts them into structured representations.

Responsibilities:

- validate PDF input
- preserve the uploaded source file
- extract text and tables with Docling
- write Markdown for human inspection
- write structured JSON for downstream processing

Primary module:

```text
src/policy_ai/ingestion/converter.py
```

### 2. Parsing

The parser converts Docling-specific output into an internal document schema.

The internal schema includes:

- document ID
- title
- source file
- sections
- page ranges
- section content

Primary module:

```text
src/policy_ai/ingestion/parser.py
```

### 3. Metadata Enrichment

The metadata stage adds retrieval-relevant information without relying on an LLM.

Current metadata includes:

- document title
- page range
- word count
- detected dates
- version placeholder
- reference placeholders

Primary module:

```text
src/policy_ai/ingestion/metadata.py
```

### 4. Chunking

PolicyAI uses section-aware chunking rather than arbitrary character windows.

Current rules:

- preserve section boundaries
- keep sections below the maximum size intact
- split long sections by paragraph
- split oversized paragraphs with controlled overlap
- remove empty chunks

Primary module:

```text
src/policy_ai/ingestion/chunker.py
```

Planned improvement:

- split legal documents by regulation or clause number
- attach regulation number and topic metadata to each chunk
- preserve tables as independent retrieval units

### 5. Embeddings

Each chunk is embedded using BGE-M3.

The embedding input combines:

```text
section heading + chunk content
```

Vectors are normalized for cosine similarity.

Primary module:

```text
src/policy_ai/ingestion/embedder.py
```

### 6. Indexing

Qdrant stores named vectors and payload metadata.

Each point contains:

- dense vector
- sparse BM25 vector
- document ID
- source filename
- section ID
- section heading
- page range
- content
- word count

Primary module:

```text
src/policy_ai/knowledge/indexer.py
```

### 7. Retrieval

Retrieval combines dense semantic search and sparse lexical search.

Process:

1. Embed the query with BGE-M3.
2. Generate a BM25 sparse query vector.
3. Query both vector spaces in Qdrant.
4. Fuse rankings with reciprocal rank fusion.
5. Rerank candidates with BGE reranker.
6. Apply a small section-heading match bonus.
7. Return the best evidence.

Primary module:

```text
src/policy_ai/retrieval/retriever.py
```

Document-specific filtering is supported through Qdrant payload filters.

### 8. Grounded Generation

The generator receives only retrieved and filtered evidence.

Generation rules include:

- answer only from supplied sources
- cite factual claims as `[Source X]`
- keep answers concise
- refuse when evidence is insufficient
- avoid unsupported external knowledge

Qwen runs locally through Ollama with thinking disabled for faster responses.

Primary module:

```text
src/policy_ai/generation/generator.py
```

### 9. Follow-Up Questions

A lightweight query rewriter converts context-dependent follow-up questions into standalone retrieval queries.

Only recent conversation turns are used to resolve references. Chat history is not treated as evidence.

Primary module:

```text
src/policy_ai/generation/query_rewriter.py
```

### 10. API and User Interface

FastAPI exposes JSON endpoints and serves an HTMX interface.

The interface supports:

- PDF upload
- document listing
- deletion
- document selection
- question answering
- source display
- loading indicators
- lightweight session history

Primary module:

```text
src/policy_ai/api/main.py
```

## Design Principles

### Inspectability

Every stage writes output that can be inspected manually. This makes it possible to identify whether an error originated in extraction, parsing, chunking, retrieval, reranking, or generation.

### Modularity

The parser, embedding model, vector database, reranker, and LLM can be replaced independently.

### Precision First

The system combines semantic and lexical retrieval because regulatory questions often require both natural-language matching and exact legal terminology.

### Grounding

The LLM is not used as the source of truth. Retrieved document evidence remains authoritative.

### Refusal Over Guessing

When retrieval confidence is too low, the system returns an explicit insufficient-evidence response.
