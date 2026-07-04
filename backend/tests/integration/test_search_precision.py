import os
import pytest
import json
from datetime import datetime
from app.services.elasticsearch_client import get_es_client, create_index, delete_index, index_chunks
from app.services.document_processor import process_document
from app.services.elasticsearch_client import search as es_search

TEST_INDEX = "test_precision"

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")

QUERIES = [
    {"q": "valid", "expected_file": "valid.pdf"},
    {"q": "custom fonts", "expected_file": "custom_fonts.pdf"},
    {"q": "empty", "expected_file": "empty.pdf"},
    {"q": "valid", "expected_file": "valid.docx"},
    {"q": "custom fonts", "expected_file": "custom_fonts.docx"},
    {"q": "empty", "expected_file": "empty.docx"},
    {"q": "corrupted", "expected_file": "corrupted.pdf"},
    {"q": "corrupted", "expected_file": "corrupted.docx"},
]


@pytest.fixture(scope="module")
def setup_test_index():
    """Создаёт индекс и индексирует все файлы из папки fixtures."""
    es = get_es_client()
    delete_index(TEST_INDEX)
    create_index(TEST_INDEX)

    for file_name in os.listdir(FIXTURES_DIR):
        if not file_name.lower().endswith(('.pdf', '.docx')):
            continue
        file_path = os.path.join(FIXTURES_DIR, file_name)
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        processed = process_document(file_name, file_bytes)
        index_chunks(file_name, file_name, processed["chunks"], index_name=TEST_INDEX)

    yield
    delete_index(TEST_INDEX)


def test_precision_at_3(setup_test_index):
    """Тест оценки Precision@3."""
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

    assert precision >= 0.7, f"Precision@3 слишком низкая: {precision:.2f}"