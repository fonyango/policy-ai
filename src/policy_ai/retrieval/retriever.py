import re
from pathlib import Path
from typing import Any

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models
from sentence_transformers import CrossEncoder, SentenceTransformer

DENSE_MODEL_NAME = "BAAI/bge-m3"
SPARSE_MODEL_NAME = "Qdrant/bm25"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"

COLLECTION_NAME = "policy_documents"
QDRANT_URL = "http://localhost:6333"


dense_model = SentenceTransformer(DENSE_MODEL_NAME)
sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)
reranker = CrossEncoder(RERANKER_MODEL_NAME)


def _section_match(query: str, section: str) -> float:
    query_terms = re.findall(r"\w+", query.lower())
    section_terms = re.findall(r"\w+", section.lower())

    matches = sum(
        any(query_term[:5] == section_term[:5] for section_term in section_terms)
        for query_term in query_terms
        if len(query_term) >= 4
    )

    return matches / max(len(query_terms), 1)


def retrieve(
    query: str,
    limit: int = 5,
    collection_name: str = COLLECTION_NAME,
    filename: str | None = None,
) -> list[dict[str, Any]]:
    query = query.strip()

    if not query:
        raise ValueError("Query cannot be empty.")

    dense_vector = dense_model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    sparse_embedding = next(sparse_model.query_embed(query))

    client = QdrantClient(url=QDRANT_URL)

    query_filter = models.Filter(
        must_not=[
            models.FieldCondition(
                key="chunk_type",
                match=models.MatchValue(value="toc"),
            )
        ]
    )

    if filename:
        safe_name = Path(filename).name
        source_file = f"{Path(safe_name).stem}_parsed_metadata_chunks.json"

        query_filter.must = [
            models.FieldCondition(
                key="source_file",
                match=models.MatchValue(value=source_file),
            )
        ]

    results = client.query_points(
        collection_name=collection_name,
        prefetch=[
            models.Prefetch(
                query=dense_vector,
                using=DENSE_VECTOR_NAME,
                limit=20,
                filter=query_filter,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_embedding.indices.tolist(),
                    values=sparse_embedding.values.tolist(),
                ),
                using=SPARSE_VECTOR_NAME,
                limit=20,
                filter=query_filter,
            ),
        ],
        query=models.FusionQuery(
            fusion=models.Fusion.RRF,
        ),
        limit=20,
        with_payload=True,
    ).points

    pairs = [
        (
            query,
            (
                f"Document: {result.payload.get('document_title', '')}\n"
                f"Section: {result.payload.get('section', '')}\n"
                f"Pages: {result.payload.get('page_start')}-"
                f"{result.payload.get('page_end')}\n\n"
                f"{result.payload.get('content', '')}"
            ),
        )
        for result in results
    ]

    rerank_scores = reranker.predict(pairs)

    reranked = []

    for result, rerank_score in zip(results, rerank_scores, strict=True):
        section_score = _section_match(
            query,
            result.payload.get("section", ""),
        )

        final_score = float(rerank_score)

        reranked.append(
            {
                "result": result,
                "rerank_score": float(rerank_score),
                "section_score": section_score,
                "final_score": final_score,
            }
        )

    reranked.sort(
        key=lambda item: item["final_score"],
        reverse=True,
    )

    return [
        {
            "score": item["final_score"],
            "rerank_score": item["rerank_score"],
            "section_score": item["section_score"],
            "section": item["result"].payload.get("section"),
            "page_start": item["result"].payload.get("page_start"),
            "page_end": item["result"].payload.get("page_end"),
            "content": item["result"].payload.get("content"),
            "document_title": item["result"].payload.get("document_title"),
        }
        for item in reranked[:limit]
    ]


if __name__ == "__main__":
    matches = retrieve(
        "What are the requirements for open tendering?",
        limit=4,
    )

    for index, match in enumerate(matches, start=1):
        print(f"\n--- Result {index} ---")
        print(f"Section: {match['section']}")
        print(f"Score: {match['score']:.4f}")
        print(match["content"])
