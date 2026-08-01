import os
from pathlib import Path
from shutil import copyfileobj
from typing import Annotated, Any
from uuid import uuid4
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models
from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime
from policy_ai.auth.models import User, UserRole

from policy_ai.auth.dependencies import get_current_user, require_admin
from policy_ai.auth.models import User
from policy_ai.auth.routes import router as auth_router
from policy_ai.database.session import get_db
from policy_ai.generation.generator import generate_answer
from policy_ai.ingestion.pipeline import process_document
from policy_ai.knowledge.models import Document

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

app = FastAPI(
    title="PolicyAI",
    version="0.1.0",
)

app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL"),
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
    document_id: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]


class DocumentSummary(BaseModel):
    id: str
    filename: str
    created_at: datetime


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
def ingest_document(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> IngestResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    document_id = str(uuid4())
    safe_name = Path(file.filename).name
    saved_name = f"{document_id}_{safe_name}"
    saved_path = raw_dir / saved_name

    with saved_path.open("wb") as destination:
        copyfileobj(file.file, destination)

    result = process_document(saved_path)

    source_file = f"{saved_path.stem}_parsed_metadata_chunks.json"

    existing_document = db.scalar(
        select(Document).where(Document.source_file == source_file)
    )

    if existing_document:
        existing_document.filename = safe_name
        existing_document.owner_id = current_user.id
    else:
        db.add(
            Document(
                id=document_id,
                filename=safe_name,
                source_file=f"{saved_path.stem}_parsed_metadata_chunks.json",
                owner_id=current_user.id,
            )
        )

    db.commit()

    return IngestResponse(
        filename=file.filename,
        indexed_chunks=result["indexed_chunks"],
        outputs=result,
    )


@app.get("/documents", response_model=list[DocumentSummary])
def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DocumentSummary]:
    query = select(Document).order_by(Document.created_at.desc())

    if current_user.role != UserRole.ADMIN.value:
        query = query.where(Document.owner_id == current_user.id)

    documents = db.scalars(query).all()

    return [
        DocumentSummary(
            id=document.id,
            filename=document.filename,
            created_at=document.created_at,
        )
        for document in documents
    ]


@app.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    safe_name = Path(document.filename).name
    stored_name = f"{document.id}_{safe_name}"
    stem = Path(stored_name).stem

    raw_path = Path("data/raw") / stored_name
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
                                value=document.source_file,
                            ),
                        )
                    ]
                )
            ),
            wait=True,
        )

    filename = document.filename

    db.delete(document)
    db.commit()

    return {
        "id": document_id,
        "filename": filename,
        "deleted_files": deleted_files,
    }


@app.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AskResponse:

    owner_id = None if current_user.role == UserRole.ADMIN.value else current_user.id
    document = None

    if request.document_id:
        document = db.get(Document, request.document_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        if (
            current_user.role != UserRole.ADMIN.value
            and document.owner_id != current_user.id
        ):
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this document.",
            )

    try:
        result = generate_answer(
            query=request.question,
            limit=request.limit,
            source_file=document.source_file if document else None,
            owner_id=owner_id,
        )

        return AskResponse(**result)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
