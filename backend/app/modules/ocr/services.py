import time
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlmodel import Session

from app.core.config import settings
from app.core.storage import MinioEngine
from app.modules.iam.users.models import User
from app.modules.ocr import repo as ocr_repo
from app.modules.ocr.models import OcrDocument
from app.modules.ocr.providers.factory import get_ocr_provider
from app.modules.ocr.schema import OcrStatus


def validate_upload(file: UploadFile) -> None:
    """Validate file MIME type before processing."""
    if file.content_type not in settings.ocr_allowed_mime_list:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File type '{file.content_type}' not allowed. "
                f"Allowed: {settings.ocr_allowed_mime_list}"
            ),
        )


async def process_document(
    *,
    session: Session,
    current_user: User,
    file: UploadFile,
    provider_name: str | None = None,
) -> OcrDocument:
    """Upload file to MinIO, run OCR, persist results."""
    validate_upload(file)

    file_bytes = await file.read()
    file_size = len(file_bytes)

    max_bytes = settings.OCR_MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size {file_size} bytes exceeds max of {settings.OCR_MAX_FILE_SIZE_MB} MB.",
        )

    doc_id = uuid.uuid4()
    extension = _get_extension(file.filename or "upload", file.content_type or "")
    minio_key = f"ocr/{current_user.id}/{doc_id}{extension}"

    minio = MinioEngine.get_instance()
    minio.upload_file(
        bucket=settings.OCR_BUCKET,
        key=minio_key,
        data=file_bytes,
        content_type=file.content_type or "application/octet-stream",
    )

    doc = OcrDocument(
        id=doc_id,
        original_filename=file.filename or "upload",
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=file_size,
        minio_key=minio_key,
        status=OcrStatus.PROCESSING.value,
        owner_id=current_user.id,
    )
    doc = ocr_repo.create(session=session, doc=doc)

    try:
        provider = get_ocr_provider(provider_name)
        start_time = time.monotonic()
        result = await provider.extract(file_bytes, doc.mime_type)
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        update_data = {
            "status": OcrStatus.COMPLETED.value,
            "extracted_text": result.markdown_text,
            "provider_used": result.provider_name,
            "page_count": result.page_count,
            "processing_time_ms": elapsed_ms,
            "completed_at": datetime.now(timezone.utc),
        }
        doc = ocr_repo.update(session=session, doc=doc, update_data=update_data)

    except Exception as exc:
        update_data = {
            "status": OcrStatus.FAILED.value,
            "error_message": str(exc),
            "completed_at": datetime.now(timezone.utc),
        }
        doc = ocr_repo.update(session=session, doc=doc, update_data=update_data)

    return doc


def list_documents(
    *,
    session: Session,
    current_user: User,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[OcrDocument], int]:
    owner_id = None if current_user.is_superuser else current_user.id
    return ocr_repo.get_multi(
        session=session, owner_id=owner_id, status=status, skip=skip, limit=limit
    )


def get_document(
    *,
    session: Session,
    current_user: User,
    doc_id: uuid.UUID,
) -> OcrDocument:
    doc = ocr_repo.get_by_id(session=session, doc_id=doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="OCR document not found")
    if not current_user.is_superuser and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return doc


def delete_document(
    *,
    session: Session,
    current_user: User,
    doc_id: uuid.UUID,
) -> None:
    doc = get_document(session=session, current_user=current_user, doc_id=doc_id)
    try:
        minio = MinioEngine.get_instance()
        minio.delete_file(bucket=settings.OCR_BUCKET, key=doc.minio_key)
    except Exception:
        pass  # Log but don't fail if MinIO deletion fails
    ocr_repo.delete(session=session, doc=doc)


def _get_extension(filename: str, mime_type: str) -> str:
    if "." in filename:
        return "." + filename.rsplit(".", 1)[-1].lower()
    mime_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/tiff": ".tiff",
        "application/pdf": ".pdf",
    }
    return mime_map.get(mime_type, "")
