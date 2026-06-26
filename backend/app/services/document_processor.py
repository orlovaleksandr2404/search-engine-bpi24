import logging
import os
import tempfile
import time
from typing import List, Tuple

import pdfplumber
from docx import Document

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    start = time.time()
    logger.info("Начало извлечения текста из PDF")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        text_parts = []
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        result = "\n".join(text_parts)
        logger.info(f"Извлечение PDF завершено за {time.time() - start:.2f} сек, длина текста {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Ошибка парсинга PDF: {e}")
        raise ValueError(f"Не удалось извлечь текст из PDF: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

def extract_text_from_docx(file_bytes: bytes) -> str:
    start = time.time()
    logger.info("Начало извлечения текста из DOCX")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        doc = Document(tmp_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        result = "\n".join(paragraphs)
        logger.info(f"Извлечение DOCX завершено за {time.time() - start:.2f} сек, длина текста {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Ошибка парсинга DOCX: {e}")
        raise ValueError(f"Не удалось извлечь текст из DOCX: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Tuple[str, int]]:
    start = time.time()
    logger.info("Начало чанкинга текста")
    if not text:
        return []
    step = chunk_size - overlap
    if step <= 0:
        step = chunk_size
    chunks = []
    for i in range(0, len(text), step):
        chunk = text[i:i + chunk_size]
        chunks.append((chunk, 1))
    logger.info(f"Чанкинг завершён, создано {len(chunks)} чанков за {time.time() - start:.2f} сек")
    return chunks

def process_document(file_name: str, file_bytes: bytes) -> dict:
    logger.info(f"process_document: начало для {file_name}")
    ext = file_name.split('.')[-1].lower()
    if ext == 'pdf':
        text = extract_text_from_pdf(file_bytes)
    elif ext == 'docx':
        text = extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Неподдерживаемый формат")
    if not text.strip():
        raise ValueError("Извлечённый текст пуст")
    chunks = chunk_text(text)
    logger.info("process_document: завершён")
    return {
        "file_name": file_name,
        "text": text,
        "chunks": chunks
    }