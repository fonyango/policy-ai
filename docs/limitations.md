# Current Limitations

PolicyAI is a functional MVP, but several capabilities are intentionally incomplete.

## 1. Regulation-Aware Chunking

The current chunker preserves section boundaries but does not consistently split documents by individual regulation, clause, schedule row, or legal provision.

Impact:

- broad sections may contain several unrelated provisions
- the correct section can rank first while the wrong passage within that section is selected
- answer completeness can suffer for detailed legal questions

Planned improvement:

- detect numbered regulations and clauses
- create one chunk per legal provision where possible
- attach regulation number, topic, parent section, and page metadata

## 2. Table Extraction Quality

Docling extraction is usable but not perfect.

Impact:

- complex multi-page tables may lose header relationships
- merged cells may be reconstructed incorrectly
- exact threshold lookups may require manual validation

Planned improvement:

- preserve tables as structured objects
- validate table schemas before indexing
- add deterministic row-level lookup for codes and thresholds

## 3. Document Versioning

The MVP does not yet track amendments, corrigenda, effective dates, or superseded documents.

Impact:

- multiple versions of the same regulation may conflict
- the system cannot reliably answer “what applied on a specific date?”
- an older document could be retrieved as if it were current

Planned improvement:

- store document lifecycle metadata in PostgreSQL
- link amendments to original documents
- filter retrieval by effective date and active status

## 4. Limited Evaluation Dataset

The current evaluation contains 15 questions based mainly on one procurement regulation document.

Impact:

- 100% retrieval accuracy should not be generalized to other documents
- the benchmark may not capture difficult table, amendment, or multi-document questions

Planned improvement:

- expand to several documents and at least 50–100 questions
- include adversarial, ambiguous, and multi-hop questions
- add independently reviewed expected answers

## 5. Answer Completeness

Current answer completeness is 84.6% under keyword-based evaluation.

Impact:

- some answers omit important details even when the correct broad section is retrieved
- exact phrase matching can also undercount semantically correct answers

Planned improvement:

- regulation-aware chunking
- alternative keyword groups
- evidence-level completeness checks
- human-reviewed answer rubrics

## 6. Local Model Dependency

The application currently uses Qwen through Ollama.

Impact:

- performance depends on local hardware
- first requests may be slower
- deployment requires Ollama or a compatible inference service

Planned improvement:

- support configurable local and hosted models
- separate generation settings from application code
- add model health checks

## 7. File-Based Metadata

Document files and processed artifacts are stored on disk. Qdrant stores retrieval vectors, but PostgreSQL is not yet used.

Impact:

- document metadata is harder to query
- lifecycle management is limited
- multi-user deployment is not yet robust

Planned improvement:

- add PostgreSQL for document, version, ingestion-run, and status metadata

## 8. No Authentication or Authorization (On Purpose)

The current interface has no login or role-based access.

Impact:

- any user with access can upload or delete documents
- unsuitable for public deployment with private documents

Planned improvement:

- authentication
- user and organization separation
- role-based upload and deletion permissions

## 9. Synchronous Ingestion

PDF processing runs inside the request lifecycle.

Impact:

- large PDFs can keep requests open for a long time
- failures may interrupt the user experience

Planned improvement:

- background job queue
- ingestion status tracking
- progress updates
- retry support

## 10. Legal and Compliance Scope

PolicyAI is a software demonstration and should not be presented as legal advice.

Impact:

- generated answers still require validation against official source documents
- critical decisions should not rely solely on model output

Recommended use:

- research assistance
- document navigation
- evidence retrieval
- internal knowledge support

Not recommended without further controls:

- autonomous legal decisions
- compliance certification
- production use where errors have legal consequences
