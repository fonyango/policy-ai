from pathlib import Path
from typing import Any

from policy_ai.ingestion.chunker import chunk_document
from policy_ai.ingestion.converter import extract_pdf_to_markdown
from policy_ai.ingestion.embedder import embed_document
from policy_ai.ingestion.metadata import enrich_metadata
from policy_ai.ingestion.parser import parse_document
from policy_ai.knowledge.indexer import index_document


def process_document(
    input_path: str | Path,
    owner_id: int,
) -> dict[str, Any]:
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    markdown_path = extract_pdf_to_markdown(pdf_path)

    docling_json_path = markdown_path.with_suffix(".json")

    parsed_path = parse_document(docling_json_path)
    metadata_path = enrich_metadata(parsed_path)
    chunks_path = chunk_document(metadata_path)
    embedded_path = embed_document(chunks_path)
    indexed_chunks = index_document(
        embedded_path,
        owner_id=owner_id,
    )

    return {
        "source": str(pdf_path),
        "markdown": str(markdown_path),
        "structured_json": str(docling_json_path),
        "parsed": str(parsed_path),
        "metadata": str(metadata_path),
        "chunks": str(chunks_path),
        "embedded": str(embedded_path),
        "indexed_chunks": indexed_chunks,
    }


if __name__ == "__main__":
    result = process_document("data/raw/procument.pdf")

    result = process_document(
        saved_path="data/raw/procument.pdf",
        owner_id=1,
    )

    for key, value in result.items():
        print(f"{key}: {value}")
