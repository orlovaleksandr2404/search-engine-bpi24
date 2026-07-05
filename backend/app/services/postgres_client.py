import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, create_engine, func
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)
Base = declarative_base()


class DocumentMeta(Base):
    """Модель SQLAlchemy для таблицы documents."""
    __tablename__ = "documents"
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="processing")
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def save_document_metadata(doc_id: uuid.UUID, file_name: str, status: str) -> None:
    """Сохраняет метаданные документа в БД."""
    session = SessionLocal()
    try:
        doc = DocumentMeta(id=doc_id, file_name=file_name, status=status)
        session.add(doc)
        session.commit()
        logger.info(f"Метаданные сохранены: {file_name} ({doc_id})")
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка сохранения: {e}")
        raise
    finally:
        session.close()


def get_documents(limit: int = 100, offset: int = 0) -> list[dict]:
    """Возвращает список документов с пагинацией."""
    session = SessionLocal()
    try:
        docs = session.query(DocumentMeta).order_by(DocumentMeta.uploaded_at.desc()).offset(offset).limit(limit).all()
        return [
            {
                "id": str(doc.id),
                "file_name": doc.file_name,
                "status": doc.status,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            }
            for doc in docs
        ]
    finally:
        session.close()


def count_documents() -> int:
    """Возвращает общее количество документов."""
    session = SessionLocal()
    try:
        return session.query(func.count(DocumentMeta.id)).scalar() or 0
    finally:
        session.close()