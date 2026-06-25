import os
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Файл {pdf_path} не найден")

    logger.info(f"Чтение PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    full_next = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            full_next.append(text)
        else:
            logger.warning(f"Страница {page_num} не содержит текста")
    return "\n".join(full_next)

def split_text_into_chunks(text: str, max_chunk_size: int = 8000) -> list[str]:
    logger.info("Разбивка текста на чанки...")
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = []
    current_size = 0
    
    for p in paragraphs:
        p_size = len(p) + 1
        
        if p_size > max_chunk_size:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0
            for i in range(0, len(p), max_chunk_size):
                chunks.append(p[i:i+max_chunk_size])
            continue
        
        if current_size + p_size > max_chunk_size:
            chunks.append("\n".join(current_chunk))
            current_chunk = [p]
            current_size = p_size
        else:
            current_chunk.append(p)
            current_size += p_size
    
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    logger.info(f"Получено {len(chunks)} чанков")
    return chunks                      