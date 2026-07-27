import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"


def embed_document(
    chunks_path: str | Path,
    output_dir: str | Path = "data/processed",
) -> Path:
    chunks_path = Path(chunks_path)
    output_dir = Path(output_dir)

    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

    document = json.loads(chunks_path.read_text(encoding="utf-8"))
    chunks = document["chunks"]

    if not chunks:
        raise ValueError("No chunks found.")

    texts = [f"{chunk['section']}\n\n{chunk['content']}" for chunk in chunks]

    model = SentenceTransformer(MODEL_NAME)

    embeddings = model.encode(
        texts,
        batch_size=8,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    for chunk, embedding in zip(chunks, embeddings, strict=True):
        chunk["embedding"] = embedding.tolist()

    document["embedding_model"] = MODEL_NAME
    document["embedding_dimension"] = len(embeddings[0])

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{chunks_path.stem}_embedded.json"
    output_path.write_text(
        json.dumps(document, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    saved_path = embed_document(
        "../data/processed/procurement_regulations_parsed_metadata_chunks.json"
    )
    print(f"Saved to: {saved_path}")

    with open(
        "../data/processed/procurement_regulations_parsed_metadata_chunks_embedded.json"
    ) as file:
        data = json.load(file)

    print("Chunks:", len(data["chunks"]))
    print("Dimension:", data["embedding_dimension"])
    print("First vector:", len(data["chunks"][0]["embedding"]))
