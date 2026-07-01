import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
<<<<<<< Updated upstream

from fastapi import APIRouter, File, HTTPException, UploadFile
from redis import asyncio as aioredis
=======
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
>>>>>>> Stashed changes

from app.config import settings
from app.models.schemas import DocumentUploadResponse
from app.services.document_processor import process_document
from app.services.elasticsearch_client import create_index, index_chunks
from app.services.postgres_client import get_documents, count_documents, save_document_metadata

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    total_start = time.time()
    logger.info("=== НАЧАЛО ЗАГРУЗКИ ===")
    filename = file.filename or "unknown"
    ext = "." + filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат. Разрешены: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    try:
        contents = await file.read()
        logger.info(f"Файл прочитан, размер {len(contents)} байт за {time.time()-total_start:.2f} сек")
    except MemoryError:
        raise HTTPException(status_code=413, detail="Файл слишком велик для обработки")
    except Exception as e:
        logger.error(f"Ошибка чтения: {e}")
        raise HTTPException(status_code=400, detail="Не удалось прочитать файл")

    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Размер превышает {settings.MAX_FILE_SIZE // (1024*1024)} МБ"
        )

    doc_id = uuid.uuid4()
    logger.info(f"UUID: {doc_id}")

    loop = asyncio.get_running_loop()
    try:
        logger.info("Начинаем обработку документа (таймаут 120 сек)...")
        processed = await asyncio.wait_for(
            loop.run_in_executor(None, process_document, filename, contents),
            timeout=120.0
        )
        chunks_count = len(processed["chunks"])
        logger.info(f"Создано {chunks_count} чанков за {time.time()-total_start:.2f} сек")
        contents = None
    except asyncio.TimeoutError:
        logger.error("Таймаут обработки документа")
        raise HTTPException(status_code=408, detail="Превышено время обработки документа")
    except ValueError as e:
        logger.error(f"Ошибка обработки: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")

    try:
        logger.info("Проверяем/создаём индекс...")
        await loop.run_in_executor(None, create_index)
        logger.info("Индексация чанков...")
        await loop.run_in_executor(None, index_chunks, str(doc_id), filename, processed["chunks"])
        logger.info("Индексация завершена")
        # Сохраняем метаданные в PostgreSQL (статус indexed)
        await loop.run_in_executor(None, save_document_metadata, doc_id, filename, "indexed")
    except Exception as e:
        logger.error(f"Ошибка индексации или сохранения: {e}")
        raise HTTPException(status_code=500, detail="Не удалось проиндексировать")

    return DocumentUploadResponse(
        document_id=doc_id,
        file_name=filename,
        status="indexed",
        uploaded_at=datetime.now(timezone.utc)
    )

<<<<<<< Updated upstream
@router.get("/search")
async def search_documents(q: str, size: int = 10):
    """
    Поиск по документам в Elasticsearch
    """
    cache_key = f"search:q:{q}:size:{size}"

    try:
        cached_res = await redis_client.get(cache_key)
        if cached_res:
            logger.info(f"--- КЭШ НАЙДЕН (Cache Hit) для запроса: '{q}' ---")
            return json.loads(cached_res)
    except Exception as e:
        logger.error(f"Ошибка при обращении к Redis: {e}")

    logger.info(f"--- КЭША НЕТ (Cache Miss). Запрос к Elasticsearch для: '{q}' ---")

    from app.config import settings
    from app.services.elasticsearch_client import get_es_client

    es = get_es_client()

    body = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["text", "file_name"],
                "fuzziness": "AUTO"
            }
        },
        "size": size
    }

    try:
        response = es.search(index=settings.ELASTICSEARCH_INDEX, body=body)
        hits = response.get("hits", {}).get("hits", [])

        max_score = 0.0
        for hit in hits:
            score = hit.get("_score", 0.0)
            if score > max_score:
                max_score = score

        results = []
        for hit in hits:
            source = hit["_source"]
            raw_score = hit.get("_score", 0.0)
            # Нормализуем: делим на max_score, если он больше 0
            normalized_score = raw_score / max_score if max_score > 0 else 0.0

            results.append({
                "chunk_id": source.get("chunk_id"),
                "file_name": source.get("file_name"),
                "page": source.get("page", 1),
                "text": source.get("text", ""),
                "score": normalized_score
            })

        search_response = {
            "results": results,
            "total": response.get("hits", {}).get("total", {}).get("value", 0),
            "page": 1,
            "page_size": size
        }
        try:
            await redis_client.setex(cache_key, 300, json.dumps(search_response))
            logger.info(f"Результаты запроса '{q}' успешно кэшированы.")
        except Exception as e:
            logger.error(f"Не удалось записать кэш в Redis: {e}")
        return search_response

    except Exception as e:
        logging.error(f"Ошибка поиска: {e}")
        raise HTTPException(status_code=500, detail="Ошибка выполнения поиска")
=======

@router.get("/")
async def list_documents(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Количество записей на страницу")
):
    """
    Возвращает список загруженных документов с пагинацией.
    Использует данные из PostgreSQL.
    """
    offset = (page - 1) * size
    items = get_documents(limit=size, offset=offset)
    total = count_documents()
    total_pages = (total + size - 1) // size if size > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": size,
        "total_pages": total_pages
    }
>>>>>>> Stashed changes
