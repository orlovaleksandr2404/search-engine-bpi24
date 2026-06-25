import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.models.schemas import DocumentUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "unknown"
    ext = "." + filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат. Разрешены: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Размер файла превышает {settings.MAX_FILE_SIZE // (1024*1024)} МБ"
        )

    doc_id = uuid.uuid4()

    logger.info(f"Файл {filename} загружен, ID={doc_id}")

    return DocumentUploadResponse(
        document_id=doc_id,
        file_name=filename,
        status="uploaded",
        uploaded_at=datetime.now(timezone.utc)
    )