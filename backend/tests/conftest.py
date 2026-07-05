import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.elasticsearch_client import create_index, delete_index, get_es_client

TEST_INDEX = "test_documents"

@pytest.fixture(scope="session")
def test_client():
    """Клиент FastAPI для тестов."""
    return TestClient(app)

@pytest.fixture(scope="function")
def es_client():
    """Клиент Elasticsearch с отдельным тестовым индексом."""
    client = get_es_client()
    delete_index(TEST_INDEX)
    create_index(TEST_INDEX)
    yield client
    delete_index(TEST_INDEX)

@pytest.fixture
def sample_pdf_bytes():
    """Байты тестового PDF-файла."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", "sample.pdf")
    if not os.path.exists(path):
        pytest.skip("Тестовый PDF не найден, пропускаем")
    with open(path, "rb") as f:
        return f.read()

@pytest.fixture
def sample_docx_bytes():
    """Байты тестового DOCX-файла."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", "sample.docx")
    if not os.path.exists(path):
        pytest.skip("Тестовый DOCX не найден, пропускаем")
    with open(path, "rb") as f:
        return f.read()