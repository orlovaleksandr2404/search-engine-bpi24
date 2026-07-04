import os
import tempfile
import logging
import time
from typing import List, Tuple

import pdfplumber
from docx import Document
import wizarddocx as wd  # <-- Новая библиотека

logger = logging.getLogger(__name__)


# ---------- Извлечение текста из PDF (постранично) ----------
def extract_text_from_pdf(file_bytes: bytes) -> List[Tuple[str, int]]:
    """
    Извлекает текст из PDF постранично.
    Возвращает список кортежей (текст_страницы, номер_страницы).
    """
    start = time.time()
    logger.info("Начало извлечения текста из PDF постранично")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        pages_text = []
        with pdfplumber.open(tmp_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages_text.append((page_text.strip(), page_num))
                else:
                    logger.warning(f"Страница {page_num} не содержит текста или пуста")

        logger.info(f"Извлечено {len(pages_text)} страниц из PDF за {time.time()-start:.2f} сек")
        return pages_text
    except Exception as e:
        logger.error(f"Ошибка парсинга PDF: {e}")
        raise ValueError(f"Не удалось извлечь текст из PDF: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ---------- Извлечение текста из DOCX (постранично) с помощью wizarddocx ----------
def extract_text_from_docx(file_bytes: bytes) -> List[Tuple[str, int]]:
    """
    Извлекает текст из DOCX постранично, используя библиотеку wizarddocx.
    Возвращает список кортежей (текст_страницы, номер_страницы).
    """
    start = time.time()
    logger.info("Начало извлечения текста из DOCX постранично (wizarddocx)")

    try:
        # wizarddocx.extract_text возвращает текст всех страниц (без разделения) если pages=None
        full_text = wd.extract_text(file_bytes, extension="docx", pages=None)

        # Разделяем страницы по символу form feed (\f) – стандартный разделитель
        if '\f' in full_text:
            pages_raw = full_text.split('\f')
        else:
            # Если разделителя нет – считаем весь текст одной страницей
            pages_raw = [full_text]

        # Формируем результат
        pages_text = []
        for idx, page_content in enumerate(pages_raw, start=1):
            if page_content and page_content.strip():
                pages_text.append((page_content.strip(), idx))

        logger.info(f"Извлечение DOCX завершено за {time.time()-start:.2f} сек, найдено {len(pages_text)} страниц")
        return pages_text

    except Exception as e:
        logger.error(f"Ошибка парсинга DOCX с wizarddocx: {e}")
        # Fallback: пробуем извлечь весь текст без страниц через python-docx
        try:
            import tempfile
            from docx import Document
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            doc = Document(tmp_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text_fallback = "\n".join(paragraphs)
            if full_text_fallback.strip():
                logger.warning("Использован fallback без страниц для DOCX")
                return [(full_text_fallback.strip(), 1)]  # весь текст на странице 1
            else:
                return []
        except Exception as fallback_err:
            logger.error(f"Fallback также не удался: {fallback_err}")
            return []


# ---------- Чанкинг текста ----------
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100, page_num: int = 1) -> List[Tuple[str, int]]:
    """
    Разбивает текст на чанки размером chunk_size с перекрытием overlap.
    Возвращает список кортежей (текст_чанка, номер_страницы).
    """
    if not text:
        return []
    chunks = []
    step = chunk_size - overlap
    if step <= 0:
        step = chunk_size
    for i in range(0, len(text), step):
        chunk = text[i:i+chunk_size]
        if chunk.strip():
            chunks.append((chunk, page_num))
    return chunks


# ---------- Основная функция обработки документа ----------
def process_document(file_name: str, file_bytes: bytes) -> dict:
    """
    Обрабатывает документ: извлекает текст постранично, разбивает на чанки с реальными номерами страниц.
    Возвращает словарь: file_name, text (полный текст), chunks (список (chunk_text, page)).
    """
    logger.info(f"process_document: начало для {file_name}")
    ext = file_name.split('.')[-1].lower()
    all_chunks = []
    full_text = ""

    if ext == 'pdf':
        pages = extract_text_from_pdf(file_bytes)
    elif ext == 'docx':
        pages = extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Неподдерживаемый формат")

    if not pages:
        raise ValueError("В документе не найдено текста")

    # Обрабатываем каждую страницу
    for page_text, page_num in pages:
        full_text += page_text + "\n"
        chunks = chunk_text(page_text, chunk_size=1000, overlap=100, page_num=page_num)
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("Не удалось создать чанки (возможно, текст слишком короткий)")

    logger.info(f"process_document: завершён, создано {len(all_chunks)} чанков")
    return {
        "file_name": file_name,
        "text": full_text,
        "chunks": all_chunks
    }