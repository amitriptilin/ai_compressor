import os
import threading
import asyncio
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from utils.logging_setup import setup_logging
from core.pdf_parser import extract_text_from_pdf, split_text_into_chunks
from core.ai_client import process_chunks
from writers.txt_writer import save_as_txt
from writers.docx_writer import save_as_word
from writers.pdf_writer import save_as_pdf

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
    "Обычный текст (.txt)": ("txt", save_as_txt),
    "Документ Word (.docx)": ("docx", save_as_word),
    "Документ PDF (.pdf)": ("pdf", save_as_pdf),
}

class AICompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Academic Compressor v2.1 (Async)")
        self.root.geometry("680x580")
        self.root.resizable(False, False)
        
        self.file_path = ""
        self.output_path = None
        self.key_visible = False
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self._build_ui()
        self._setup_logging()
    
    def _setup_logging(self):
        setup_logging()
    
    def _build_ui(self):
        file_frame = ttk.LabelFrame(self.root, text=" 1. Исходный PDF ", padding=10)
        file_frame.pack(fill="x", padx=15, pady=10)
        
        self.btn_browse = ttk.Button(file_frame, text="Выбрать PDF", command=self.browse_file)
        self.btn_browse.pack(side="left", padx=5)
        
        self.lbl_file = ttk.Label(file_frame, text="Файл не выбран", foreground="gray")
        self.lbl_file.pack(side="left", padx=10, fill="x", expand=True)
        
        key_frame = ttk.LabelFrame(self.root, text=" 2. API-ключ OpenRouter ", padding=10)
        key_frame.pack(fill="x", padx=15, pady=5)
        
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=50, show="*")
        self.key_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.btn_toggle_key = ttk.Button(key_frame, text="👁️", width=4, command=self.toggle_key_visibility)
        self.btn_toggle_key.pack(side="right", padx=5)
        
        ttk.Label(key_frame, text="Получить ключ на https://openrouter.ai/keys", foreground="gray", font=("Arial", 8)).pack(side="bottom", anchor="w", pady=2)

        settings_frame = ttk.LabelFrame(self.root, text=" 3. Настройки обработки ", padding=10)
        settings_frame.pack(fill="x", padx=15, pady=5)
        
        ttk.Label(settings_frame, text="Степень сжатия:").grid(row=0, column=0, sticky="w", pady=5)
        self.comp_var = tk.StringVar(value="Среднее")
        comp_combo = ttk.Combobox(settings_frame, textvariable=self.comp_var, values=list(COMPRESSION_OPTIONS.keys()), state="readonly", width=40)
        comp_combo.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Сложность лексики:").grid(row=1, column=0, sticky="w", pady=5)
        self.simp_var = tk.StringVar(value="Для студента")
        simp_combo = ttk.Combobox(settings_frame, textvariable=self.simp_var, values=list(SIMPLICITY_OPTIONS.keys()), state="readonly", width=40)
        simp_combo.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Формат сохранения:").grid(row=2, column=0, sticky="w", pady=5)
        self.format_var = tk.StringVar(value="Документ Word (.docx)")
        format_combo = ttk.Combobox(settings_frame, textvariable=self.format_var, values=list(FORMAT_MAP.keys()), state="readonly", width=40)
        format_combo.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Параллельных запросов:").grid(row=3, column=0, sticky="w", pady=5)
        self.concurrent_var = tk.IntVar(value=5)
        concurrent_spinbox = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.concurrent_var, width=5)
        concurrent_spinbox.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.btn_start = ttk.Button(action_frame, text="ПОЕХАЛИ!", command=self.start_processing)
        self.btn_start.pack(fill="x", pady=5)
        
        self.lbl_status = ttk.Label(action_frame, text="Статус: Ожидание", font=("Arial", 10, "bold"))
        self.lbl_status.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(action_frame, mode="determinate", maximum=100)
        self.progress_bar.pack(fill="x", pady=5)
    
    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.file_path = path
            self.lbl_file.config(text=os.path.basename(path), foreground="black")
    
    def toggle_key_visibility(self):
        if self.key_visible:
            self.key_entry.config(show="*")
            self.btn_toggle_key.config(text="👁️")
        else:
            self.key_entry.config(show="")
            self.btn_toggle_key.config(text="🙈")
        self.key_visible = not self.key_visible
    
    def start_processing(self):
        api_key = self.key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Внимание", "Введите API-ключ OpenRouter!")
            return
        
        if not self.file_path:
            messagebox.showwarning("Внимание", "Выберите PDF-файл")
            return
        
        fmt_key = self.format_var.get()
        ext = FORMAT_MAP[fmt_key][0]
        default_name = os.path.splitext(os.path.basename(self.file_path))[0] + "_compressed." + ext
        out_path = filedialog.asksaveasfilename(
            initialdir=os.path.dirname(self.file_path),
            initialfile=default_name,
            defaultextension="." + ext,
            filetypes=[(fmt_key, f"*.{ext}")]
        )
        if not out_path:
            return
        self.output_path = out_path
        
        self.btn_start.config(state="disabled")
        self.btn_browse.config(state="disabled")
        self.key_entry.config(state="disabled")
        self.progress_bar["value"] = 0
        self.lbl_status.config(text="Статус: Обработка...")
        
        threading.Thread(target=self._run_async, args=(api_key,), daemon=True).start()
    
    def _run_async(self, api_key):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process(api_key))
        finally:
            loop.close()
    
    async def _process(self, api_key):
        try:
            self._update_status("Чтение PDF...")
            raw_text = extract_text_from_pdf(self.file_path)
            chunks = split_text_into_chunks(raw_text)
            if not chunks:
                raise RuntimeError("В PDF не найден текст")
            
            compression_prompt = COMPRESSION_OPTIONS[self.comp_var.get()]
            simplicity_prompt = SIMPLICITY_OPTIONS[self.simp_var.get()]
            concurrent = self.concurrent_var.get()
            
            total = len(chunks)
            def progress_callback(current, total):
                self.root.after(0, lambda: self._update_progress(current, total))
            
            self._update_status(f"Обработка {total} чанков через DeepSeek (параллельно {concurrent})...")
            final_text = await process_chunks(
                chunks,
                compression_prompt,
                simplicity_prompt,
                api_key=api_key,
                progress_callback=progress_callback,
                max_concurrent=concurrent
            )
            
            fmt_key = self.format_var.get()
            _, writer_func = FORMAT_MAP[fmt_key]
            writer_func(final_text, self.output_path)
            
            self.root.after(0, self._finish_success)
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))
    
    def _update_progress(self, current, total):
        self.progress_bar["value"] = (current / total) * 100
        self.lbl_status.config(text=f"Статус: обработано {current}/{total} чанков")
    
    def _update_status(self, msg):
        self.root.after(0, lambda: self.lbl_status.config(text=f"Статус: {msg}"))
    
    def _finish_success(self):
        self.btn_start.config(state="normal")
        self.btn_browse.config(state="normal")
        self.key_entry.config(state="normal")
        self.progress_bar["value"] = 100
        self.lbl_status.config(text="Статус: Готово!")
        messagebox.showinfo("Успех", f"Результат сохранён:\n{self.output_path}")
    
    def _show_error(self, msg):
        self.btn_start.config(state="normal")
        self.btn_browse.config(state="normal")
        self.key_entry.config(state="normal")
        self.progress_bar["value"] = 0
        self.lbl_status.config(text="Статус: Ошибка")
        messagebox.showerror("Ошибка", msg)

def main():
    root = tk.Tk()
    app = AICompressorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()