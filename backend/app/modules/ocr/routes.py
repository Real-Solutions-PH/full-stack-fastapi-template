import uuid
from typing import Any

from fastapi import APIRouter, File, Query, UploadFile

from app.modules.iam.deps import CurrentUser
from app.modules.ocr import services as ocr_service
from app.modules.ocr.providers.factory import list_available_providers
from app.modules.ocr.schema import OcrDocumentPublic, OcrDocumentsPublic
from app.shared.deps import SessionDep
from app.shared.schema import Message

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/upload", response_model=OcrDocumentPublic)
async def upload_document(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    provider: str | None = Query(default=None, description="OCR provider to use"),
) -> Any:
    """Upload a document image and run OCR processing."""
    doc = await ocr_service.process_document(
        session=session,
        current_user=current_user,
        file=file,
        provider_name=provider,
    )
    return doc


@router.get("/", response_model=OcrDocumentsPublic)
def list_documents(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    status: str | None = Query(default=None, description="Filter by status"),
) -> Any:
    """List OCR documents for the current user."""
    docs, count = ocr_service.list_documents(
        session=session,
        current_user=current_user,
        status=status,
        skip=skip,
        limit=limit,
    )
    items = [OcrDocumentPublic.model_validate(d) for d in docs]
    return OcrDocumentsPublic(data=items, count=count)


@router.get("/providers", response_model=list[str])
def get_available_providers(
    current_user: CurrentUser,  # noqa: ARG001
) -> Any:
    """List available OCR providers."""
    return list_available_providers()


@router.get("/{id}", response_model=OcrDocumentPublic)
def get_document(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """Get a single OCR document by ID."""
    return ocr_service.get_document(
        session=session, current_user=current_user, doc_id=id
    )


@router.delete("/{id}")
def delete_document(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """Delete an OCR document and its MinIO file."""
    ocr_service.delete_document(
        session=session, current_user=current_user, doc_id=id
    )
    return Message(message="OCR document deleted successfully")
