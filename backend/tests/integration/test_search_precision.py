import json
import logging
import os
from datetime import datetime

import pytest

from app.services.document_processor import process_document
from app.services.elasticsearch_client import create_index, delete_index, get_es_client, index_chunks
from app.services.elasticsearch_client import search as es_search

logger = logging.getLogger(__name__)
TEST_INDEX = "test_precision"
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")

def extract_query_from_file(file_path: str) -> str:
    """Извлекает первые 5 слов из файла для использования в качестве поискового запроса."""
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            from app.services.document_processor import extract_text_from_pdf
            pages = extract_text_from_pdf(file_bytes)
            full_text = " ".join([text for text, _ in pages])
        elif ext == '.docx':
            from app.services.document_processor import extract_text_from_docx_fallback
            full_text = extract_text_from_docx_fallback(file_bytes)
        else:
            return ""
        words = full_text.split()
        return " ".join(words[:5]) if words else ""
    except Exception as e:
        logger.warning(f"Не удалось извлечь текст из {file_path}: {e}")
        return ""

def build_queries_from_files(fixtures_dir):
    queries = []
    if not os.path.exists(fixtures_dir):
        return queries
    for fname in os.listdir(fixtures_dir):
        if not fname.lower().endswith(('.pdf', '.docx')):
            continue
        file_path = os.path.join(fixtures_dir, fname)
        query = extract_query_from_file(file_path)
        if query:
            queries.append({"q": query, "expected_file": fname})
    return queries

QUERIES = build_queries_from_files(FIXTURES_DIR)

@pytest.fixture(scope="module")
def setup_test_index():
    es = get_es_client()
    delete_index(TEST_INDEX)
    create_index(TEST_INDEX)

    if not os.path.exists(FIXTURES_DIR):
        pytest.skip(f"Папка с фикстурами не найдена: {FIXTURES_DIR}")

    indexed_count = 0
    for file_name in os.listdir(FIXTURES_DIR):
        if not file_name.lower().endswith(('.pdf', '.docx')):
            continue
        file_path = os.path.join(FIXTURES_DIR, file_name)
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            processed = process_document(file_name, file_bytes)
            index_chunks(file_name, file_name, processed["chunks"], index_name=TEST_INDEX)
            indexed_count += 1
            logger.info(f"Индексирован файл: {file_name}")
        except Exception as e:
            logger.warning(f"Не удалось проиндексировать файл {file_name}: {e}")

    if indexed_count == 0:
        pytest.skip("Нет доступных файлов для индексации")

    es.indices.refresh(index=TEST_INDEX)
    logger.info(f"Индекс {TEST_INDEX} обновлён (refresh)")

    yield
    delete_index(TEST_INDEX)

def test_precision_at_3(setup_test_index):
    if not QUERIES:
        pytest.skip("Нет запросов для проверки (не удалось извлечь текст из файлов)")

    results = []
    for query in QUERIES:
        q = query["q"]
        expected = query["expected_file"]
        search_result = es_search(q, size=3, index_name=TEST_INDEX)
        hits = search_result["results"]
        found = any(hit["file_name"] == expected for hit in hits)
        top3_names = [h["file_name"] for h in hits]
        results.append({
            "query": q,
            "expected_file": expected,
            "found_in_top3": found,
            "actual_top3": top3_names
        })

    precision = sum(1 for r in results if r["found_in_top3"]) / len(results) if results else 0.0

    print("\n" + "="*60)
    print("Оценка качества поиска (Precision@3)")
    print("="*60)
    for r in results:
        status = "✅" if r["found_in_top3"] else "❌"
        msg = (f"{status} Запрос: '{r['query']}' | Ожидаемый: {r['expected_file']} | "
               f"Топ-3: {', '.join(r['actual_top3'])}")
        print(msg)
    print("="*60)
    print(f"Precision@3 = {precision:.2f}")
    print("="*60)

    report = {
        "timestamp": datetime.now().isoformat(),
        "precision_at_3": precision,
        "details": results
    }
    report_path = os.path.join(os.path.dirname(__file__), "precision_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Отчёт сохранён в {report_path}")

    assert precision >= 0.5, f"Precision@3 слишком низкая: {precision:.2f}"