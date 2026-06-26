import io
import logging
from typing import List, Tuple

import pdfplumber
from docx import Document

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Tuple[str, int]]:
    if not text:
        return []
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    total = len(words)
    while start < total:
        end = start
        length = 0
        while end < total and length + len(words[end]) + 1 <= chunk_size:
            length += len(words[end]) + 1
            end += 1
        if end == start:
            end = start + 1
        chunk_text = " ".join(words[start:end])
        chunks.append((chunk_text, 1))
        overlap_chars = overlap
        overlap_words = 0
        for i in range(end - 1, start - 1, -1):
            overlap_chars -= len(words[i]) + 1
            if overlap_chars <= 0:
                overlap_words = end - i
                break
        start = end - overlap_words if overlap_words > 0 else end
    return chunks

def process_document(file_name: str, file_bytes: bytes) -> dict:
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
    return {
        "file_name": file_name,
        "text": text,
        "chunks": chunks
    }