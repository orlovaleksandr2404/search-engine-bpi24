import asyncio
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.models.schemas import DocumentUploadResponse
from app.services.document_processor import process_document
from app.services.elasticsearch_client import create_index, index_chunks

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    logger.info("НАЧАЛО ЗАГРУЗКИ")

    filename = file.filename or "unknown"
    ext = "." + filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат. Разрешены: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    logger.info(f"Расширение {ext} разрешено")

    try:
        contents = await file.read()
    except MemoryError:
        logger.error("Недостаточно памяти для чтения файла")
        raise HTTPException(status_code=413, detail="Файл слишком велик для обработки")
    except Exception as e:
        logger.error(f"Ошибка чтения файла: {e}")
        raise HTTPException(status_code=400, detail="Не удалось прочитать файл")

    logger.info(f"Файл прочитан, размер: {len(contents)} байт")

    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Размер файла превышает {settings.MAX_FILE_SIZE // (1024*1024)} МБ"
        )

    doc_id = uuid.uuid4()
    logger.info(f"Сгенерирован UUID: {doc_id}")

    try:
        logger.info("Начинаем парсинг и чанкинг...")
        processed = await asyncio.to_thread(process_document, filename, contents)
        chunks_count = len(processed["chunks"])
        logger.info(f"Создано {chunks_count} чанков")
        contents = None
    except ValueError as e:
        logger.error(f"Ошибка обработки документа: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    try:
        logger.info("Создаём/проверяем индекс...")
        await asyncio.to_thread(create_index)
        logger.info("Начинаем индексацию чанков...")
        await asyncio.to_thread(index_chunks, str(doc_id), filename, processed["chunks"])
        logger.info("Индексация завершена")
    except Exception as e:
        logger.error(f"Ошибка индексации: {e}")
        raise HTTPException(status_code=500, detail="Не удалось проиндексировать документ")

    response = DocumentUploadResponse(
        document_id=doc_id,
        file_name=filename,
        status="indexed",
        uploaded_at=datetime.now(timezone.utc)
    )
    logger.info("ЗАГРУЗКА УСПЕШНО ЗАВЕРШЕНА")
    return response