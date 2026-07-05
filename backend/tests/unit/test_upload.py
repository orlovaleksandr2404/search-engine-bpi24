from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.documents import upload_document
from app.config import settings


@pytest.mark.asyncio
async def test_upload_invalid_extension():
    """Неверное расширение файла."""
    file = AsyncMock()
    file.filename = "file.txt"
    with pytest.raises(HTTPException) as exc:
        await upload_document(file)
    assert exc.value.status_code == 400
    assert "Неподдерживаемый формат" in exc.value.detail

@pytest.mark.asyncio
async def test_upload_too_large():
    """Слишком большой файл."""
    file = AsyncMock()
    file.filename = "large.pdf"
    file.read = AsyncMock(return_value=b"x" * (settings.MAX_FILE_SIZE + 1))
    with pytest.raises(HTTPException) as exc:
        await upload_document(file)
    assert exc.value.status_code == 400
    assert "размер превышает" in exc.value.detail.lower()

@pytest.mark.asyncio
@patch("app.api.v1.documents.process_document")
@patch("app.api.v1.documents.index_chunks")
@patch("app.api.v1.documents.create_index")
async def test_upload_success(mock_create, mock_index, mock_process, sample_pdf_bytes):
    """Успешная загрузка."""
    file = AsyncMock()
    file.filename = "sample.pdf"
    file.read = AsyncMock(return_value=sample_pdf_bytes)
    mock_process.return_value = {
        "file_name": "sample.pdf",
        "text": "dummy",
        "chunks": [("dummy chunk", 1)]
    }
    response = await upload_document(file)
    assert response.status == "indexed"
    assert response.file_name == "sample.pdf"
    assert response.document_id is not None