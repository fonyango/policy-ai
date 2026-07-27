import json
from pathlib import Path
from uuid import uuid4

MAX_WORDS = 800
SPLIT_SIZE = 600
OVERLAP = 100
MIN_WORDS = 20


def _count_words(text: str) -> int:
    return len(text.split())


def _split_large_text(text: str) -> list[str]:
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + SPLIT_SIZE
        chunks.append(" ".join(words[start:end]))

        if end >= len(words):
            break

        start = end - OVERLAP

    return chunks


def _split_section(content: str) -> list[str]:
    if _count_words(content) <= MAX_WORDS:
        return [content]

    paragraphs = [
        paragraph.strip() for paragraph in content.split("\n\n") if paragraph.strip()
    ]

    chunks = []
    current_paragraphs = []
    current_word_count = 0

    for paragraph in paragraphs:
        paragraph_word_count = _count_words(paragraph)

        if paragraph_word_count > MAX_WORDS:
            if current_paragraphs:
                chunks.append("\n\n".join(current_paragraphs))
                current_paragraphs = []
                current_word_count = 0

            chunks.extend(_split_large_text(paragraph))
            continue

        if current_word_count + paragraph_word_count > MAX_WORDS:
            chunks.append("\n\n".join(current_paragraphs))
            current_paragraphs = []
            current_word_count = 0

        current_paragraphs.append(paragraph)
        current_word_count += paragraph_word_count

    if current_paragraphs:
        chunks.append("\n\n".join(current_paragraphs))

    return chunks


def chunk_document(
    metadata_path: str | Path,
    output_dir: str | Path = "data/processed",
) -> Path:
    metadata_path = Path(metadata_path)
    output_dir = Path(output_dir)

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    document = json.loads(metadata_path.read_text(encoding="utf-8"))

    chunks = []

    for section in document["sections"]:
        content = section.get("content", "").strip()

        if not content:
            continue

        section_chunks = _split_section(content)
        chunk_count = len(section_chunks)

        section_chunks = [
            chunk.strip()
            for chunk in section_chunks
            if _count_words(chunk.strip()) >= MIN_WORDS
        ]
        for index, content in enumerate(section_chunks, start=1):
            chunks.append(
                {
                    "chunk_id": str(uuid4()),
                    "document_id": document["document_id"],
                    "document_title": document["title"],
                    "section_id": section["id"],
                    "section": section["heading"],
                    "page_start": section["page_start"],
                    "page_end": section["page_end"],
                    "chunk_index": index,
                    "chunk_count": chunk_count,
                    "content": content,
                    "word_count": _count_words(content),
                    "metadata": section.get("metadata", {}),
                }
            )

    output = {
        "document_id": document["document_id"],
        "document_title": document["title"],
        "source_file": document["source_file"],
        "chunk_count": len(chunks),
        "chunks": chunks,
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{metadata_path.stem}_chunks.json"
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    saved_path = chunk_document(
        "../data/processed/procurement_regulations_parsed_metadata.json"
    )
    print(f"Saved to: {saved_path}")

    import json
    from pathlib import Path

    path = Path("../data/processed/procurement_regulations_parsed_metadata_chunks.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    chunks = data["chunks"]

    print("Chunk count:", len(chunks))
    print("Empty chunks:", sum(not chunk["content"].strip() for chunk in chunks))
    print("Largest chunk:", max(chunk["word_count"] for chunk in chunks))
    print("Smallest chunk:", min(chunk["word_count"] for chunk in chunks))
