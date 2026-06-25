import os
import tempfile
import asyncio
import streamlit as st
from pathlib import Path

from utils.logging_setup import setup_logging
from core.pdf_parser import extract_text_from_pdf, split_text_into_chunks
from core.ai_client import process_chunks
from writers.txt_writer import save_as_txt
from writers.docx_writer import save_as_word
from writers.pdf_writer import save_as_pdf

setup_logging()

COMPRESSION_OPTIONS = {
    "Максимальное": "Выдели только ключевые формулы, методы, результаты и выводы. Максимально кратко.",
    "Среднее": "Сделай подробное структурированное резюме, сохранив логику исследования.",
    "Минимальное": "Убери только явные повторы и разжевывание, сохрани максимум деталей."
}

SIMPLICITY_OPTIONS = {
    "Для новичка": "Научно-популярный стиль, очень простой язык. Перепиши сложные академические обороты простыми словами.",
    "Для студента": "Понятный академический стиль для студентов младших курсов.",
    "Оригинальный": "Сохраняй строгий оригинальный язык научной статьи."
}

FORMAT_MAP = {
    "txt": ("txt", save_as_txt),
    "docx": ("docx", save_as_word),
    "pdf": ("pdf", save_as_pdf),
}

def main():
    st.set_page_config(page_title="AI Academic Compressor", page_icon="📚", layout="centered")
    st.title("📚 AI Academic Compressor")
    st.markdown("Сжимайте и упрощайте академические тексты из PDF с помощью DeepSeek")
    
    with st.sidebar:
        st.header("⚙️ Настройки")
        api_key = st.text_input("🔑 API-ключ OpenRouter", type="password", help="Получить на https://openrouter.ai/keys")
        compression_label = st.selectbox("Степень сжатия", list(COMPRESSION_OPTIONS.keys()))
        simplicity_label = st.selectbox("Сложность лексики", list(SIMPLICITY_OPTIONS.keys()))
        format_label = st.selectbox("Формат сохранения", ["txt", "docx", "pdf"], index=1)
        st.markdown("---")
        st.caption("💡 Все данные обрабатываются локально, ключ не сохраняется.")
    
    uploaded_file = st.file_uploader("📄 Загрузите PDF-файл", type=["pdf"])
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
            tmp_input.write(uploaded_file.read())
            input_path = tmp_input.name
        
        st.success(f"Файл загружен: {uploaded_file.name}")
        
        if st.button("🚀 Запустить обработку", type="primary"):
            if not api_key:
                st.error("Введите API-ключ")
                st.stop()
            
            compression_prompt = COMPRESSION_OPTIONS[compression_label]
            simplicity_prompt = SIMPLICITY_OPTIONS[simplicity_label]
            output_ext = format_label
            _, writer_func = FORMAT_MAP[output_ext]
            
            log_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            try:
                log_placeholder.info("📖 Извлечение текста из PDF...")
                raw_text = extract_text_from_pdf(input_path)
                chunks = split_text_into_chunks(raw_text)
                if not chunks:
                    st.error("Не удалось извлечь текст из PDF")
                    st.stop()
                
                total = len(chunks)
                completed = 0
                def progress_callback(current, total):
                    nonlocal completed
                    completed += 1
                    progress_bar.progress(completed / total)
                    log_placeholder.info(f"Обработано {completed}/{total} чанков")
                
                log_placeholder.info(f"🔄 Обработка {total} чанков через DeepSeek...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    final_text = loop.run_until_complete(
                        process_chunks(
                            chunks,
                            compression_prompt,
                            simplicity_prompt,
                            api_key=api_key,
                            progress_callback=progress_callback
                        )
                    )
                finally:
                    loop.close()
                
                log_placeholder.info("💾 Сохранение результата...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_ext}") as tmp_output:
                    output_path = tmp_output.name
                writer_func(final_text, output_path)
                
                with open(output_path, "rb") as f:
                    file_data = f.read()
                
                st.success("✅ Готово!")
                st.download_button(
                    label=f"📥 Скачать результат ({uploaded_file.name.replace('.pdf', f'_compressed.{output_ext}')})",
                    data=file_data,
                    file_name=uploaded_file.name.replace(".pdf", f"_compressed.{output_ext}"),
                    mime="application/octet-stream"
                )
                
                os.unlink(input_path)
                os.unlink(output_path)
                
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
            finally:
                progress_bar.empty()
    
    st.markdown("---")
    st.caption("🚀 Работает на основе DeepSeek через OpenRouter API.")

if __name__ == "__main__":
    main()