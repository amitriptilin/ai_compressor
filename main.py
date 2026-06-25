import asyncio
import click
import logging
from pathlib import Path
from utils.logging_setup import setup_logging
from utils.key_manager import get_api_key
from core.pdf_parser import extract_text_from_pdf, split_text_into_chunks
from core.ai_client import process_chunks
from writers.txt_writer import save_as_txt
from writers.docx_writer import save_as_word
from writers.pdf_writer import save_as_pdf

COMPRESSION_MAP = {
    "max": "Выдели только ключевые формулы, методы, результаты и выводы. Максимально кратко.",
    "mid": "Сделай подробное структурированное резюме, сохранив логику исследования.",
    "min": "Убери только явные повторы и разжевывание, сохрани максимум деталей."
}

SIMPLICITY_MAP = {
    "novice": "Научно-популярный стиль, очень простой язык. Перепиши сложные академические обороты простыми словами.",
    "student": "Понятный академический стиль для студентов младших курсов.",
    "original": "Сохраняй строгий оригинальный язык научной статьи."
}

@click.command()
@click.argument("pdf", type=click.Path(exists=True, dir_okay=False))
@click.option("--compression", "-c", type=click.Choice(["max", "mid", "min"]), default="mid", help="Степень сжатия")
@click.option("--simplicity", "-s", type=click.Choice(["novice", "student", "original"]), default="student", help="Уровень лексики")
@click.option("--output", "-o", type=click.Path(writable=True), help="Путь к выходному файлу (расширение определит формат)")
@click.option("--format", "-f", type=click.Choice(["txt", "docx", "pdf"]), default="docx", help="Формат вывода (если не указан output)")
@click.option("--key", envvar="OPENROUTER_API_KEY", help="API-ключ (можно задать через переменную окружения OPENROUTER_API_KEY)")
@click.option("--concurrent", "-p", default=5, help="Максимальное число параллельных запросов (по умолчанию 5)")
def cli(pdf, compression, simplicity, output, format, key, concurrent):
    setup_logging()
    log = logging.getLogger(__name__)
    
    if not key:
        key = get_api_key(interactive=True)
    
    if not output:
        output = Path(pdf).stem + f"_compressed.{format}"
        if format == "docx":
            output += "x"
    else:
        ext = Path(output).suffix.lower()
        if ext in [".txt"]:
            format = "txt"
        elif ext in [".docx"]:
            format = "docx"
        elif ext in [".pdf"]:
            format = "pdf"
        else:
            raise click.BadParameter(f"Неподдерживаемое расширение: {ext}. Используйте .txt, .docx или .pdf")
    
    log.info(f"Обработка файла: {pdf}")
    log.info(f"Сжатие: {compression}, Сложность: {simplicity}")
    
    raw_text = extract_text_from_pdf(pdf)
    chunks = split_text_into_chunks(raw_text)
    if not chunks:
        log.error("Не удалось извлечь текст из PDF")
        return
    
    compression_prompt = COMPRESSION_MAP[compression]
    simplicity_prompt = SIMPLICITY_MAP[simplicity]
    
    def progress_callback(current, total):
        print(f"\rОбработано {current}/{total} чанков", end="", flush=True)
    
    log.info(f"Запуск асинхронной обработки с параллельностью {concurrent}...")
    final_text = asyncio.run(
        process_chunks(
            chunks,
            compression_prompt,
            simplicity_prompt,
            api_key=key,
            progress_callback=progress_callback,
            max_concurrent=concurrent
        )
    )
    print()
    
    if format == "txt":
        save_as_txt(final_text, output)
    elif format == "docx":
        save_as_word(final_text, output)
    elif format == "pdf":
        save_as_pdf(final_text, output)
    
    log.info(f"Готово! Результат: {output}")

if __name__ == "__main__":
    cli()