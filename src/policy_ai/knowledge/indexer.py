import json
from pathlib import Path
import os

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()


COLLECTION_NAME = "policy_documents"
QDRANT_URL = os.getenv("QDRANT_URL")
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
SPARSE_MODEL_NAME = "Qdrant/bm25"


def index_document(
    embedded_path: str | Path,
    collection_name: str = COLLECTION_NAME,
) -> int:
    embedded_path = Path(embedded_path)

    if not embedded_path.exists():
        raise FileNotFoundError(f"Embedded file not found: {embedded_path}")

    document = json.loads(embedded_path.read_text(encoding="utf-8"))
    chunks = document.get("chunks", [])
    vector_size = document.get("embedding_dimension")

    if not chunks:
        raise ValueError("No embedded chunks found.")

    if not vector_size:
        raise ValueError("Embedding dimension is missing.")

    client = QdrantClient(url=QDRANT_URL)

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            DENSE_VECTOR_NAME: models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            )
        },
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: models.SparseVectorParams(
                modifier=models.Modifier.IDF,
            )
        },
    )

    texts = [f"{chunk['section']}\n\n{chunk['content']}" for chunk in chunks]

    sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)
    sparse_embeddings = list(sparse_model.embed(texts))

    points = [
        models.PointStruct(
            id=chunk["chunk_id"],
            vector={
                DENSE_VECTOR_NAME: chunk["embedding"],
                SPARSE_VECTOR_NAME: models.SparseVector(
                    indices=sparse_embedding.indices.tolist(),
                    values=sparse_embedding.values.tolist(),
                ),
            },
            payload={
                "document_id": chunk["document_id"],
                "document_title": chunk["document_title"],
                "source_file": document["source_file"],
                "section_id": chunk["section_id"],
                "section": chunk["section"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                "word_count": chunk["word_count"],
                "chunk_type": chunk.get("chunk_type", "content"),
                **chunk.get("metadata", {}),
            },
        )
        for chunk, sparse_embedding in zip(
            chunks,
            sparse_embeddings,
            strict=True,
        )
    ]

    client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True,
    )

    return len(points)


if __name__ == "__main__":
    indexed_count = index_document(
        "data/processed/procument_parsed_metadata_chunks_embedded.json"
    )
    print(f"Indexed chunks: {indexed_count}")

    from qdrant_client import QdrantClient

    client = QdrantClient(url="http://localhost:6333")

    result = client.count(
        collection_name="policy_documents",
        exact=True,
    )

    print(result.count)
