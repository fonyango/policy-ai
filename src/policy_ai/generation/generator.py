from typing import Any

from ollama import chat

from policy_ai.retrieval.retriever import expand_with_neighbors, retrieve

MODEL_NAME = "qwen3:8b"
MIN_RELEVANCE_SCORE = 0.15


def _build_context(results: list[dict[str, Any]]) -> str:
    sections = []

    for index, result in enumerate(results, start=1):
        sections.append(
            f"[Source {index}]\n"
            f"Document: {result['document_title']}\n"
            f"Section: {result['section']}\n"
            f"Pages: {result['page_start']}-{result['page_end']}\n"
            f"Content:\n{result['content']}"
        )

    return "\n\n".join(sections)


def generate_answer(
    query: str,
    limit: int = 5,
    sources: list[dict[str, Any]] | None = None,
    filename: str | None = None,
) -> dict[str, Any]:
    query = query.strip()

    if not query:
        raise ValueError("Query cannot be empty.")

    if sources is None:
        sources = retrieve(
            query=query,
            limit=limit,
            filename=filename,
        )

    if not sources:
        return {
            "answer": "I could not find enough evidence in the indexed documents.",
            "sources": [],
        }

    if sources[0]["score"] < MIN_RELEVANCE_SCORE:
        return {
            "answer": "I could not find enough evidence in the indexed documents.",
            "sources": [],
        }

    top_source = sources[0]
    sources = expand_with_neighbors(top_source)

    if not sources:
        return {
            "answer": "I could not find enough evidence in the indexed documents.",
            "sources": [],
        }

    context = _build_context(sources)

    response = chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer only from the supplied sources. "
                    "Answer the exact question concisely. "
                    "Keep the answer under 150 words. "
                    "Separate direct requirements from supporting procedures when necessary. "
                    "Cite every factual claim only as [Source 1], [Source 2], and so on. "
                    "Include relevant section or regulation numbers when they are directly supported by the sources. "
                    "Every sentence containing factual information must end with a [Source X] citation. "
                    "If the sources are insufficient, say so."
                ),
            },
            {
                "role": "user",
                "content": f"Question:\n{query}\n\nSources:\n{context}",
            },
        ],
        think=False,
        options={
            "temperature": 0,
            "num_predict": 250,
        },
    )

    formatted_sources = [
        {
            "document_title": source["document_title"],
            "section": source["section"],
            "page_start": source["page_start"],
            "page_end": source["page_end"],
            "score": round(source["score"], 4),
        }
        for source in sources
    ]

    return {
        "answer": response.message.content,
        "sources": formatted_sources,
    }


if __name__ == "__main__":
    result = generate_answer("What are the requirements for open tendering?")

    print(result["answer"])
