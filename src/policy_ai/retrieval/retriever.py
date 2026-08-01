import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models
from sentence_transformers import CrossEncoder, SentenceTransformer

load_dotenv()

DENSE_MODEL_NAME = "BAAI/bge-m3"
SPARSE_MODEL_NAME = "Qdrant/bm25"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"

COLLECTION_NAME = "policy_documents"
QDRANT_URL = os.getenv("QDRANT_URL")


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


def expand_with_neighbors(
    source: dict[str, Any],
    collection_name: str = COLLECTION_NAME,
) -> list[dict[str, Any]]:
    chunk_index = source.get("chunk_index")

    if chunk_index is None:
        return [source]

    client = QdrantClient(url=QDRANT_URL)

    records, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=source["document_id"]),
                ),
                models.FieldCondition(
                    key="section_id",
                    match=models.MatchValue(value=source["section_id"]),
                ),
                models.FieldCondition(
                    key="chunk_index",
                    match=models.MatchAny(
                        any=[
                            chunk_index - 1,
                            chunk_index,
                            chunk_index + 1,
                        ]
                    ),
                ),
            ]
        ),
        limit=3,
        with_payload=True,
        with_vectors=False,
    )

    records.sort(key=lambda record: record.payload["chunk_index"])

    return [
        {
            **source,
            "chunk_index": record.payload["chunk_index"],
            "section": record.payload["section"],
            "page_start": record.payload["page_start"],
            "page_end": record.payload["page_end"],
            "content": record.payload["content"],
            "document_title": record.payload["document_title"],
        }
        for record in records
    ]


def retrieve(
    query: str,
    limit: int = 5,
    collection_name: str = COLLECTION_NAME,
    source_file: str | None = None,
    owner_id: int | None = None,
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

    must_conditions = []

    if source_file:
        must_conditions.append(
            models.FieldCondition(
                key="source_file",
                match=models.MatchValue(value=source_file),
            )
        )

    if owner_id is not None:
        must_conditions.append(
            models.FieldCondition(
                key="owner_id",
                match=models.MatchValue(value=owner_id),
            )
        )

    query_filter = models.Filter(
        must=must_conditions or None,
        must_not=[
            models.FieldCondition(
                key="chunk_type",
                match=models.MatchValue(value="toc"),
            )
        ],
    )

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
            "document_id": item["result"].payload.get("document_id"),
            "section_id": item["result"].payload.get("section_id"),
            "chunk_index": item["result"].payload.get("chunk_index"),
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
