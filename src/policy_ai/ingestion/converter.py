from pathlib import Path
import json
from docling.document_converter import DocumentConverter


def extract_pdf_to_markdown(
    pdf_path: str | Path,
    output_dir: str | Path = "data/processed",
) -> Path:
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    output_dir.mkdir(parents=True, exist_ok=True)

    converter = DocumentConverter()
    result = converter.convert(pdf_path)

    markdown = result.document.export_to_markdown()
    json_content = result.document.export_to_dict()

    json_path = output_dir / f"{pdf_path.stem}.json"
    json_path.write_text(
        json.dumps(json_content, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    output_path = output_dir / f"{pdf_path.stem}.md"
    output_path.write_text(markdown, encoding="utf-8")

    return output_path


if __name__ == "__main__":
    saved_path = extract_pdf_to_markdown("data/raw/procurement_regulations.pdf")
    print(f"Saved to: {saved_path}")
