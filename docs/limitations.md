# Current Limitations

PolicyAI is a functional MVP, but several areas still need improvement.

## Main Limitations

- **Small evaluation set:** Results are based on 15 questions and should not be generalized broadly.
- **Table extraction:** Complex tables may lose structure or require manual validation.
- **Document versioning:** Amendments, effective dates, and superseded documents are not yet tracked.
- **Synchronous ingestion:** Large PDF uploads are processed inside the API request.
- **Local model dependency:** Qwen runs through Ollama, so performance depends on local hardware.
- **SQLite for development:** The current relational database is suitable for local use, not large multi-user deployment.
- **No persistent chat history:** Conversations are not stored across sessions.
- **Limited account features:** Refresh tokens, password reset, and organization-level access are not yet implemented.
- **Legal scope:** Answers are for research and document navigation, not legal advice.

## Planned Improvements

- Background ingestion jobs and progress tracking
- PostgreSQL for production metadata
- Better table handling and deterministic lookup
- Amendment and version tracking
- Larger evaluation datasets
- Persistent chat history
- Configurable local and hosted LLMs
- Stronger account and organization controls
