import pytest
import os
import datetime
import json
from app.services.elasticsearch_client import get_es_client, index_chunks, create_index, delete_index
from app.services.document_processor import process_document
from app.services.elasticsearch_client import search as es_search

TEST_INDEX = "test_precision"

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "test_documents")

QUERIES = [
    {"q": "математика", "expected_file": "math_lecture.pdf"},
    {"q": "физика", "expected_file": "physics_lecture.pdf"},
    {"q": "история", "expected_file": "history_lecture.pdf"},
]

@pytest.fixture(scope="module")
def setup_test_index():
    """Создаёт индекс и индексирует тестовые документы."""
    es = get_es_client()
    delete_index(TEST_INDEX)
    create_index(TEST_INDEX)

    for file_name in os.listdir(FIXTURES_DIR):
        if not file_name.endswith(('.pdf', '.docx')):
            continue
        file_path = os.path.join(FIXTURES_DIR, file_name)
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        processed = process_document(file_name, file_bytes)
        doc_id = file_name
        index_chunks(doc_id, file_name, processed["chunks"], index_name=TEST_INDEX)

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
        results.append({
            "query": q,
            "expected_file": expected,
            "found_in_top3": found,
            "actual_top3": [h["file_name"] for h in hits]
        })

    precision = sum(1 for r in results if r["found_in_top3"]) / len(results)
    print(f"Precision@3 = {precision:.2f}")

    assert precision >= 0.7, f"Precision@3 too low: {precision:.2f}"

    report = {
        "timestamp": datetime.now().isoformat(),
        "precision_at_3": precision,
        "details": results
    }
    with open("precision_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)