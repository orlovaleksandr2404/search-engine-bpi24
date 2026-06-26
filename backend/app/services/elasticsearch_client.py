import logging
import re
from typing import List, Tuple

from elasticsearch import Elasticsearch

from app.config import settings

logger = logging.getLogger(__name__)

_es_client = None

def get_es_client():
    global _es_client
    if _es_client is None:
        _es_client = Elasticsearch(
            [f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"]
        )
    return _es_client

def create_index(index_name: str = None):
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
                "file_name": {"type": "text"},
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

def clean_text(text: str) -> str:
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

def index_chunks(doc_id: str, file_name: str, chunks: List[Tuple[str, int]], index_name: str = None):
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