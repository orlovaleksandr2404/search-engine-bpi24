import os
import sys
import json
import logging
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.elasticsearch_client import get_es_client, create_index, delete_index, index_chunks
from app.services.document_processor import process_document
from app.services.elasticsearch_client import search as es_search

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TEST_INDEX = "precision_eval"
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures")

QUERIES = [
    {"q": "valid", "expected_file": "valid.pdf"},
    {"q": "valid", "expected_file": "valid.docx"},
    {"q": "custom fonts", "expected_file": "custom_fonts.pdf"},
    {"q": "custom fonts", "expected_file": "custom_fonts.docx"},
    {"q": "corrupted", "expected_file": "corrupted.pdf"},
    {"q": "corrupted", "expected_file": "corrupted.docx"},
    {"q": "empty", "expected_file": "empty.pdf"},
    {"q": "empty", "expected_file": "empty.docx"},
]

def main():
    if not os.path.exists(FIXTURES_DIR):
        logger.error(f"Папка с фикстурами не найдена: {FIXTURES_DIR}")
        return

    es = get_es_client()
    delete_index(TEST_INDEX)
    create_index(TEST_INDEX)

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
            logger.info(f"Индексирован: {file_name}")
        except Exception as e:
            logger.warning(f"Пропускаем файл {file_name}: {e}")

    if indexed_count == 0:
        logger.error("Нет файлов для индексации")
        return

    results = []
    for q in QUERIES:
        res = es_search(q["q"], size=3, index_name=TEST_INDEX)
        top3 = [h["file_name"] for h in res["results"]]
        found = q["expected_file"] in top3
        results.append({
            "query": q["q"],
            "expected": q["expected_file"],
            "top3": top3,
            "found": found
        })

    precision = sum(r["found"] for r in results) / len(results) if results else 0.0

    print("\n" + "="*60)
    print("Оценка качества поиска (Precision@3)")
    print("="*60)
    for r in results:
        status = "✅" if r["found"] else "❌"
        print(f"{status} Запрос: '{r['query']}' | Ожидаемый: {r['expected']} | Топ-3: {', '.join(r['top3'])}")
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

if __name__ == "__main__":
    main()