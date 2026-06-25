import logging

logger = logging.getLogger(__name__)

def save_as_txt(text: str, output_path: str) -> None:
    with open(output_path, "w", encoding = "utf-8") as f:
        f.write(text)
    logger.info(f"Сохранено в TXT: {output_path}")