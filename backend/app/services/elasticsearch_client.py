import logging
from typing import List, Tuple

from elasticsearch import Elasticsearch, helpers
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
    if es.indices.exists(index=index_name):
        logger.info(f"Индекс {index_name} уже существует")
        return
    body = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "russian_analyzer": {
                        "type": "russian",
                        "stopwords": "_russian_"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "file_name": {"type": "text", "analyzer": "russian_analyzer"},
                "page": {"type": "integer"},
                "text": {"type": "text", "analyzer": "russian_analyzer"}
            }
        }
    }
    es.indices.create(index=index_name, body=body)
    logger.info(f"Индекс {index_name} создан")

def index_chunks(doc_id: str, file_name: str, chunks: List[Tuple[str, int]], index_name: str = None):
    if index_name is None:
        index_name = settings.ELASTICSEARCH_INDEX
    es = get_es_client()
    actions = []
    for i, (chunk_text, page) in enumerate(chunks):
        chunk_id = f"{doc_id}_{i}"
        actions.append({
            "_index": index_name,
            "_id": chunk_id,
            "_source": {
                "chunk_id": chunk_id,
                "file_name": file_name,
                "page": page,
                "text": chunk_text
            }
        })
    if actions:
        helpers.bulk(es, actions)
        logger.info(f"Проиндексировано {len(actions)} чанков для документа {file_name}")