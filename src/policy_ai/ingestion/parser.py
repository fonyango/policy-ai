import json
from pathlib import Path
from uuid import uuid4

from docling_core.types.doc import DoclingDocument

HEADING_LABELS = {"title", "section_header"}


def _get_page_number(item) -> int | None:
    if not getattr(item, "prov", None):
        return None

    return item.prov[0].page_no


def parse_document(
    json_path: str | Path,
    output_dir: str | Path = "data/processed",
) -> Path:
    json_path = Path(json_path)
    output_dir = Path(output_dir)

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    document = DoclingDocument.load_from_json(json_path)

    title = document.name
    sections = []
    current_section = None

    for item, _level in document.iterate_items():
        text = getattr(item, "text", "").strip()

        if not text:
            continue

        label = str(getattr(item, "label", ""))
        page_number = _get_page_number(item)

        if label == "title":
            title = text
            continue

        if label == "section_header":
            current_section = {
                "id": str(uuid4()),
                "heading": text,
                "content": [],
                "page_start": page_number,
                "page_end": page_number,
            }
            sections.append(current_section)
            continue

        if current_section is None:
            current_section = {
                "id": str(uuid4()),
                "heading": "Document introduction",
                "content": [],
                "page_start": page_number,
                "page_end": page_number,
            }
            sections.append(current_section)

        current_section["content"].append(text)

        if page_number is not None:
            if current_section["page_start"] is None:
                current_section["page_start"] = page_number

            current_section["page_end"] = page_number

    for section in sections:
        section["content"] = "\n\n".join(section["content"])

    parsed_document = {
        "document_id": str(uuid4()),
        "source_file": json_path.name,
        "title": title,
        "sections": sections,
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{json_path.stem}_parsed.json"
    output_path.write_text(
        json.dumps(parsed_document, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    saved_path = parse_document("data/processed/procurement_regulations.json")
    print(f"Saved to: {saved_path}")
