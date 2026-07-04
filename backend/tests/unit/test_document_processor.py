import pytest
from app.services.document_processor import (
    chunk_text,
    process_document,
    extract_text_from_pdf,
    extract_text_from_docx
)

def test_chunk_text():
    """Проверка разбиения на чанки с перекрытием."""
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    assert len(chunks) == 3
    for chunk, page in chunks:
        assert page == 1
    assert len(chunks[0][0]) == 1000
    assert len(chunks[1][0]) == 1000

def test_process_document_pdf(sample_pdf_bytes):
    """Проверка обработки PDF."""
    result = process_document("sample.pdf", sample_pdf_bytes)
    assert "file_name" in result
    assert "text" in result
    assert "chunks" in result
    assert len(result["chunks"]) > 0
    pages = set(chunk[1] for chunk in result["chunks"])
    assert len(pages) > 1, "PDF должен содержать несколько страниц"

def test_process_document_docx(sample_docx_bytes):
    """Проверка обработки DOCX."""
    result = process_document("sample.docx", sample_docx_bytes)
    assert result["file_name"] == "sample.docx"
    assert len(result["chunks"]) > 0

def test_extract_text_from_pdf(sample_pdf_bytes):
    """Извлечение текста из PDF."""
    pages = extract_text_from_pdf(sample_pdf_bytes)
    assert len(pages) > 0
    for text, page in pages:
        assert isinstance(text, str)
        assert isinstance(page, int)

def test_extract_text_from_docx(sample_docx_bytes):
    """Извлечение текста из DOCX (по страницам, если библиотека поддерживает)."""
    pages = extract_text_from_docx(sample_docx_bytes)
    assert len(pages) > 0
    for text, page in pages:
        assert text.strip() != ""

def test_process_document_invalid_extension():
    """Неверное расширение файла."""
    with pytest.raises(ValueError, match="Неподдерживаемый формат"):
        process_document("file.txt", b"dummy")