from pathlib import Path
from shutil import copyfileobj
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models

from policy_ai.generation.generator import generate_answer
from policy_ai.ingestion.pipeline import process_document

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "policy_documents"

app = FastAPI(
    title="PolicyAI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestResponse(BaseModel):
    filename: str
    indexed_chunks: int
    outputs: dict[str, Any]


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    limit: int = Field(default=5, ge=1, le=10)
    filename: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]


class DocumentSummary(BaseModel):
    filename: str
    source: str
    processed_files: list[str]


def get_document_summaries() -> list[dict[str, Any]]:
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")

    if not raw_dir.exists():
        return []

    documents = []

    for pdf_path in sorted(raw_dir.glob("*.pdf")):
        processed_files = [
            str(path)
            for path in sorted(processed_dir.glob(f"{pdf_path.stem}*"))
            if path.is_file()
        ]

        documents.append(
            {
                "filename": pdf_path.name,
                "source": str(pdf_path),
                "processed_files": processed_files,
            }
        )

    return documents


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "PolicyAI API",
        "docs": "/docs",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/documents", response_model=IngestResponse)
def ingest_document(file: UploadFile = File(...)) -> IngestResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name
    saved_path = raw_dir / safe_name

    with saved_path.open("wb") as destination:
        copyfileobj(file.file, destination)

    result = process_document(saved_path)

    return IngestResponse(
        filename=file.filename,
        indexed_chunks=result["indexed_chunks"],
        outputs=result,
    )


@app.get("/documents", response_model=list[DocumentSummary])
def list_documents() -> list[DocumentSummary]:
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")

    if not raw_dir.exists():
        return []

    documents = []

    for pdf_path in sorted(raw_dir.glob("*.pdf")):
        stem = pdf_path.stem

        processed_files = [
            str(path)
            for path in sorted(processed_dir.glob(f"{stem}*"))
            if path.is_file()
        ]

        documents.append(
            DocumentSummary(
                filename=pdf_path.name,
                source=str(pdf_path),
                processed_files=processed_files,
            )
        )

    return documents


@app.delete("/documents/{filename}")
def delete_document(filename: str) -> dict[str, Any]:
    safe_name = Path(filename).name
    stem = Path(safe_name).stem

    raw_path = Path("data/raw") / safe_name
    processed_dir = Path("data/processed")

    deleted_files = []

    if raw_path.exists():
        raw_path.unlink()
        deleted_files.append(str(raw_path))

    for path in processed_dir.glob(f"{stem}*"):
        if path.is_file():
            path.unlink()
            deleted_files.append(str(path))

    client = QdrantClient(url=QDRANT_URL)

    if client.collection_exists(COLLECTION_NAME):
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="source_file",
                            match=models.MatchValue(
                                value=f"{stem}_parsed_metadata_chunks.json"
                            ),
                        )
                    ]
                )
            ),
            wait=True,
        )

    if not deleted_files:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "filename": safe_name,
        "deleted_files": deleted_files,
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        result = generate_answer(
            query=request.question,
            limit=request.limit,
            filename=request.filename,
        )
        return AskResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
