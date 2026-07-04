import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.elasticsearch_client import get_es_client, create_index, delete_index, index_chunks
from app.services.document_processor import process_document
from app.services.elasticsearch_client import search as es_search
import json

TEST_INDEX = "precision_eval"
FIXTURES_DIR = "tests/fixtures/test_documents"

QUERIES = [
    {"q": "математика", "expected_file": "math_lecture.pdf"},
]

def main():
    es = get_es_client()
    delete_index(TEST_INDEX)
    create_index(TEST_INDEX)

    for fname in os.listdir(FIXTURES_DIR):
        if not fname.endswith(('.pdf', '.docx')):
            continue
        with open(os.path.join(FIXTURES_DIR, fname), "rb") as f:
            data = f.read()
        processed = process_document(fname, data)
        index_chunks(fname, fname, processed["chunks"], index_name=TEST_INDEX)

    results = []
    for q in QUERIES:
        res = es_search(q["q"], size=3, index_name=TEST_INDEX)
        hits = [h["file_name"] for h in res["results"]]
        found = q["expected_file"] in hits
        results.append({"query": q["q"], "expected": q["expected_file"], "top3": hits, "found": found})

    precision = sum(r["found"] for r in results) / len(results)
    print("Оценка качества поиска (Precision@3)")
    print("=" * 60)
    for r in results:
        print(f"Запрос: {r['query']} | Ожидаемый: {r['expected']} | В топ-3: {r['found']} | Топ-3: {', '.join(r['top3'])}")
    print("=" * 60)
    print(f"Precision@3 = {precision:.2f}")

    with open("precision_report.json", "w") as f:
        json.dump({"queries": results, "precision": precision}, f, indent=2)

if __name__ == "__main__":
    main()