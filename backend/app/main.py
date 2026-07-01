import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import documents, search
from app.services.postgres_client import Base, engine

# ---------- Настройка логирования ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ---------- Lifespan (инициализация БД при старте) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы в PostgreSQL, если их нет (синхронная операция)
    # Для асинхронности можно обернуть в run_in_executor, но при старте это некритично
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы PostgreSQL проверены/созданы")
    yield
    # Здесь можно добавить код завершения (закрытие пулов и т.п.)
    logger.info("Завершение работы приложения")


# ---------- Создание приложения (один раз!) ----------
app = FastAPI(
    title="Поисковая система по базе знаний",
    lifespan=lifespan,
)

# ---------- Middleware ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Подключение роутеров ----------
app.include_router(documents.router)
app.include_router(search.router)

# ---------- Мониторинг (Prometheus) ----------
Instrumentator().instrument(app).expose(app)

# ---------- Эндпоинт для проверки здоровья ----------
@app.get("/health")
async def health():
    return {"status": "ok"}


logger.info("Приложение запущено")
