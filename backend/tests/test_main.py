import os
import sys
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.main import app

client = TestClient(app)

def test_infrastructure_readiness():
    response = client.get("/metrics")
    assert response.status_code == 200, "Prometheus инструмент не инициализировался"
    assert "http_requests_total" in response.text, "Метрики запросов не собираются"

    assert settings.MAX_FILE_SIZE > 0, "Критическая ошибка: лимит размера файлов равен нулю"
    assert len(settings.ALLOWED_EXTENSIONS) > 0, "Критическая ошибка: список разрешенных расширений пуст"

    assert os.getenv("REDIS_HOST") is not None or settings.REDIS_HOST == "redis", \
        "Конфигурация сети Docker: бэкенд не видит хост Redis"
