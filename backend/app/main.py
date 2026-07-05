"""
Главный модуль приложения FastAPI.

Создаёт экземпляр приложения, настраивает CORS, подключает роутеры,
инициализирует базу данных через lifespan и включает мониторинг Prometheus.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import documents, search
from app.services.postgres_client import Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы PostgreSQL проверены/созданы")
    yield
    logger.info("Завершение работы приложения")


app = FastAPI(
    title="Поисковая система по базе знаний",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(search.router)

Instrumentator().instrument(app).expose(app)

@app.get("/health")
async def health():
    return {"status": "ok"}


logger.info("Приложение запущено")
