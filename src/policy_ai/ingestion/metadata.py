import json
import re
from pathlib import Path

DATE_PATTERN = r"\b\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}\b"


def enrich_metadata(
    parsed_path: str | Path,
    output_dir: str | Path = "data/processed",
) -> Path:
    parsed_path = Path(parsed_path)
    output_dir = Path(output_dir)

    document = json.loads(parsed_path.read_text(encoding="utf-8"))

    title = document["title"]

    for section in document["sections"]:
        text = section["content"]

        section["metadata"] = {
            "document_title": title,
            "page_range": f"{section['page_start']}-{section['page_end']}",
            "word_count": len(text.split()),
            "effective_dates": re.findall(DATE_PATTERN, text),
            "contains_table": False,
            "references": [],
            "version": "original",
        }

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{parsed_path.stem}_metadata.json"
    output_path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


if __name__ == "__main__":
    path = enrich_metadata("data/processed/procurement_regulations_parsed.json")
    print(path)
