import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from redis.asyncio import Redis

from app.config import settings
from app.dependencies import get_redis_client
from app.services.elasticsearch_client import get_es_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["search"])


@router.get("/search")
async def search_documents(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    file_name: Optional[str] = Query(None, description="Фильтр по точному имени файла"),
    page_min: Optional[int] = Query(None, ge=1, description="Минимальный номер страницы"),
    page_max: Optional[int] = Query(None, ge=1, description="Максимальный номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Количество результатов на страницу"),
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
    redis_client: Redis = Depends(get_redis_client)
):
    cache_key = f"search:{q}:{file_name}:{page_min}:{page_max}:{size}:{page}"
    logger.info(f"Поиск: '{q}', фильтры: file_name={file_name}, страницы {page_min}-{page_max}")

    # Проверка кеша
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache HIT для ключа {cache_key}")
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis недоступен: {e}")

    logger.info("Cache MISS. Выполняем запрос к Elasticsearch")

    es = get_es_client()
    from_ = (page - 1) * size

    must = []
    if q:
        must.append({
            "multi_match": {
                "query": q,
                "fields": ["text^1", "file_name^3"],
                "fuzziness": "AUTO",
                "operator": "and",
                "minimum_should_match": "70%"
            }
        })

    filters = []
    if file_name:
        filters.append({"term": {"file_name.keyword": file_name}})
    if page_min is not None or page_max is not None:
        range_filter = {}
        if page_min is not None:
            range_filter["gte"] = page_min
        if page_max is not None:
            range_filter["lte"] = page_max
        filters.append({"range": {"page": range_filter}})

    body = {
        "query": {"bool": {"must": must, "filter": filters}},
        "size": size,
        "from": from_,
        "track_total_hits": True,
        "timeout": "3s",
        "sort": [{"_score": {"order": "desc"}}, {"chunk_id": {"order": "asc"}}],
        "highlight": {
            "fields": {
                "text": {
                    "fragment_size": 200,
                    "number_of_fragments": 1,
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }
            }
        }
    }

    try:
        response = es.search(index=settings.ELASTICSEARCH_INDEX, body=body)
    except Exception as e:
        logger.error(f"Ошибка Elasticsearch: {e}")
        raise HTTPException(status_code=503, detail="Поисковая система временно недоступна")

    hits = response.get("hits", {}).get("hits", [])
    total = response.get("hits", {}).get("total", {}).get("value", 0)

    # Вычисляем общее количество страниц
    total_pages = (total + size - 1) // size if size > 0 else 0
    # Корректируем page, чтобы не выходить за пределы
    if page > total_pages and total_pages > 0:
        page = total_pages
        # Можно также вернуть 404, но лучше вернуть последнюю страницу

    max_score = max((hit.get("_score", 0) for hit in hits), default=0.0)
    results = []
    for hit in hits:
        source = hit["_source"]
        highlight = hit.get("highlight", {}).get("text", [source.get("text", "")])
        text_highlight = highlight[0] if highlight else source.get("text", "")
        results.append({
            "chunk_id": source.get("chunk_id"),
            "file_name": source.get("file_name"),
            "page": source.get("page", 1),
            "text": text_highlight,
            "score": hit.get("_score", 0.0) / max_score if max_score > 0 else 0.0
        })

    search_response = {
        "results": results,
        "total": total,
        "page": page,
        "page_size": size,
        "total_pages": total_pages,
        "took_ms": response.get("took", 0)
    }

    try:
        await redis_client.setex(cache_key, 300, json.dumps(search_response))
        logger.info(f"Результаты кэшированы для {cache_key}")
    except Exception as e:
        logger.warning(f"Не удалось кэшировать: {e}")

    return search_response
