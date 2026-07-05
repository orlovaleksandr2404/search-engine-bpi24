"""
Pydantic-схемы для валидации запросов и сериализации ответов.

Используются во всех эндпоинтах для гарантии структуры данных.
"""

from datetime import datetime

from pydantic import UUID4, BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: UUID4
    file_name: str
    status: str
    uploaded_at: datetime