import os
import pytest
import json
import logging
from datetime import datetime
from app.services.elasticsearch_client import get_es_client, create_index, delete_index, index_chunks
from app.services.document_processor import process_document
from app.services.elasticsearch_client import search as es_search

logger = logging.getLogger(__name__)
TEST_INDEX = "test_precision"

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")

# ---- Динамически формируем QUERIES на основе реальных файлов ----
def build_queries_from_files(fixtures_dir):
    """Создаёт список запросов: для каждого файла используем имя без расширения как запрос,
    а ожидаемым файлом является полное имя файла."""
    queries = []
    if not os.path.exists(fixtures_dir):
        return queries
    for fname in os.listdir(fixtures_dir):
        if not fname.lower().endswith(('.pdf', '.docx')):
            continue
        # Запрос – имя файла без расширения (например, "valid" для "valid.pdf")
        base = os.path.splitext(fname)[0]
        queries.append({"q": base, "expected_file": fname})
    return queries

QUERIES = build_queries_from_files(FIXTURES_DIR)


@pytest.fixture(scope="module")
def setup_test_index():
    """Создаёт индекс, индексирует все файлы и принудительно обновляет индекс."""
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

    # !!! ПРИНУДИТЕЛЬНЫЙ REFRESH !!!
    es.indices.refresh(index=TEST_INDEX)
    logger.info(f"Индекс {TEST_INDEX} обновлён (refresh)")

    yield
    delete_index(TEST_INDEX)


def test_precision_at_3(setup_test_index):
    """Тест оценки Precision@3."""
    if not QUERIES:
        pytest.skip("Нет запросов для проверки (нет файлов в fixtures)")

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
        print(f"{status} Запрос: '{r['query']}' | Ожидаемый: {r['expected_file']} | Топ-3: {', '.join(r['actual_top3'])}")
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