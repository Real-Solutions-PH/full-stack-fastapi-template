import uuid
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class OcrStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    RECEIPT = "receipt"
    INVOICE = "invoice"
    FORM = "form"
    RECIPE = "recipe"
    GENERAL = "general"
    UNKNOWN = "unknown"


class OcrDocumentBase(SQLModel):
    original_filename: str = Field(max_length=500)
    mime_type: str = Field(max_length=100)


class OcrDocumentPublic(OcrDocumentBase):
    id: uuid.UUID
    status: OcrStatus
    document_type: str | None = None
    extracted_text: str | None = None
    provider_used: str | None = None
    page_count: int | None = None
    processing_time_ms: int | None = None
    error_message: str | None = None
    file_size_bytes: int = 0
    minio_key: str
    owner_id: uuid.UUID
    created_at: datetime | None = None
    completed_at: datetime | None = None


class OcrDocumentsPublic(SQLModel):
    data: list[OcrDocumentPublic]
    count: int
