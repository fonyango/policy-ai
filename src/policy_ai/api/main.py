from typing import Any

from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models
from pathlib import Path
from shutil import copyfileobj
from markdown import markdown
from fastapi import File, UploadFile
from policy_ai.config import settings
from fastapi.responses import HTMLResponse

from policy_ai.ingestion.pipeline import process_document

from policy_ai.generation.generator import generate_answer

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

import os

from starlette.middleware.sessions import SessionMiddleware
from policy_ai.generation.query_rewriter import rewrite_query

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "policy_documents"

app = FastAPI(
    title="PolicyAI",
    version="0.1.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=False,
)

app.mount(
    "/static",
    StaticFiles(directory="src/policy_ai/static"),
    name="static",
)

templates = Jinja2Templates(directory="src/policy_ai/templates")


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
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


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


@app.get("/ui/documents", response_class=HTMLResponse)
def documents_ui(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="partials/documents.html",
        context={"documents": get_document_summaries()},
    )


@app.post("/ui/documents", response_class=HTMLResponse)
def upload_document_ui(
    request: Request,
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return templates.TemplateResponse(
            request=request,
            name="partials/upload_error.html",
            context={"message": "Only PDF files are supported."},
            status_code=400,
        )

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name
    saved_path = raw_dir / safe_name

    try:
        with saved_path.open("wb") as destination:
            copyfileobj(file.file, destination)

        process_document(saved_path)

        return templates.TemplateResponse(
            request=request,
            name="partials/upload_result.html",
            context={"filename": safe_name},
            headers={"HX-Trigger": "documentsChanged"},
        )

    except Exception as exc:
        saved_path.unlink(missing_ok=True)

        return templates.TemplateResponse(
            request=request,
            name="partials/upload_error.html",
            context={"message": f"Failed to process {safe_name}: {exc}"},
            status_code=500,
        )


@app.post("/ui/ask", response_class=HTMLResponse)
def ask_ui(
    request: Request,
    question: str = Form(...),
    document: str = Form(default=""),
):
    history = request.session.get("conversation", [])

    standalone_query = rewrite_query(
        question=question,
        history=history,
    )

    result = generate_answer(
        query=standalone_query,
        filename=document or None,
    )

    history.append(
        {
            "question": question,
            "answer": result["answer"],
        }
    )

    request.session["conversation"] = history[-3:]

    return templates.TemplateResponse(
        request=request,
        name="partials/answer.html",
        context={
            "question": question,
            "answer": markdown(result["answer"]),
            "sources": result["sources"],
        },
    )


@app.delete("/ui/documents/{filename}", response_class=HTMLResponse)
def delete_document_ui(
    request: Request,
    filename: str,
):
    delete_document(filename)

    return templates.TemplateResponse(
        request=request,
        name="partials/documents.html",
        context={"documents": get_document_summaries()},
        headers={"HX-Trigger": "documentsChanged"},
    )


@app.get("/ui/document-options", response_class=HTMLResponse)
def document_options_ui(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="partials/document_options.html",
        context={
            "documents": get_document_summaries(),
        },
    )
