import logging
import re
from typing import List, Tuple

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

from app.config import settings

logger = logging.getLogger(__name__)

_es_client = None

def get_es_client():
    """Возвращает клиент Elasticsearch."""
    global _es_client
    if _es_client is None:
        _es_client = Elasticsearch(
            [f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"]
        )
    return _es_client

def create_index(index_name: str = None):
    """Создаёт индекс Elasticsearch, если он не существует."""
    if index_name is None:
        index_name = settings.ELASTICSEARCH_INDEX
    es = get_es_client()
    try:
        es.indices.get(index=index_name)
        logger.info(f"Индекс {index_name} уже существует")
        return
    except Exception:
        logger.info("Индекс не найден, создаём новый")

    body = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "file_name": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}},
                "page": {"type": "integer"},
                "text": {"type": "text"}
            }
        }
    }
    try:
        es.indices.create(index=index_name, body=body)
        logger.info(f"Индекс {index_name} создан")
    except Exception as e:
        logger.error(f"Ошибка создания индекса: {e}")
        raise

def delete_index(index_name: str = None):
    """Удаляет индекс Elasticsearch."""
    if index_name is None:
        index_name = settings.ELASTICSEARCH_INDEX
    es = get_es_client()
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        logger.info(f"Индекс {index_name} удалён")
    else:
        logger.warning(f"Индекс {index_name} не существует")

def clean_text(text: str) -> str:
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

def index_chunks(doc_id: str, file_name: str, chunks: List[Tuple[str, int]], index_name: str = None):
    """
    Индексирует чанки документа в Elasticsearch.

    Args:
        doc_id (str): Идентификатор документа (UUID).
        file_name (str): Имя файла.
        chunks (List[Tuple[str, int]]): Список чанков (текст, страница).
        index_name (str): Имя индекса (по умолчанию из настроек).
    """
    if index_name is None:
        index_name = settings.ELASTICSEARCH_INDEX
    es = get_es_client()
    actions = []
    for i, (chunk_text, page) in enumerate(chunks):
        clean_chunk = clean_text(chunk_text)
        if not clean_chunk.strip():
            continue
        chunk_id = f"{doc_id}_{i}"
        actions.append({
            "_index": index_name,
            "_id": chunk_id,
            "_source": {
                "chunk_id": chunk_id,
                "file_name": file_name,
                "page": int(page),
                "text": clean_chunk
            }
        })
    if not actions:
        logger.warning("Нет чанков для индексации")
        return
    for action in actions:
        try:
            es.index(index=action["_index"], id=action["_id"], body=action["_source"])
        except Exception as e:
            logger.error(f"Ошибка индексации чанка {action['_id']}: {e}")
            raise
    logger.info(f"Проиндексировано {len(actions)} чанков")

def search(query: str, size: int = 10, from_: int = 0, index_name: str = None) -> dict:
    """
    Выполняет полнотекстовый поиск по индексу.
    Возвращает словарь с ключами 'results' и 'total'.
    """
    if index_name is None:
        index_name = settings.ELASTICSEARCH_INDEX
    es = get_es_client()
    try:
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["text", "file_name"],
                    "fuzziness": "AUTO"
                }
            },
            "size": size,
            "from": from_,
            "track_total_hits": True
        }
        response = es.search(index=index_name, body=body)
        hits = response.get("hits", {}).get("hits", [])
        total = response.get("hits", {}).get("total", {}).get("value", 0)
        results = []
        for hit in hits:
            source = hit["_source"]
            results.append({
                "chunk_id": source.get("chunk_id"),
                "file_name": source.get("file_name"),
                "page": source.get("page", 1),
                "text": source.get("text", ""),
                "score": hit.get("_score", 0.0)
            })
        return {"results": results, "total": total}
    except NotFoundError:
        logger.warning(f"Индекс {index_name} не найден, возвращаем пустой результат")
        return {"results": [], "total": 0}
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        raise