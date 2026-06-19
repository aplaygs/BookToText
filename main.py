#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BookToText — Конвертер электронных книг и документов в текст (.txt)"""

import os
import sys
import threading
import concurrent.futures
from tkinter import filedialog, END
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES

from converters.text_cleaner import clean_text, safe_save_path
from converters.epub_converter import convert_epub
from converters.fb2_converter import convert_fb2
from converters.pdf_converter import convert_pdf
from converters.docx_converter import convert_docx
from converters.mobi_converter import convert_mobi
from converters.rtf_converter import convert_rtf
from converters.html_converter import convert_html
from converters.metadata_extractor import extract_metadata

# Поддерживаемые расширения
SUPPORTED_EXTENSIONS = {
    '.epub': convert_epub,
    '.fb2': convert_fb2,
    '.pdf': convert_pdf,
    '.docx': convert_docx,
    '.mobi': convert_mobi,
    '.azw3': convert_mobi,
    '.azw': convert_mobi,
    '.rtf': convert_rtf,
    '.html': convert_html,
    '.htm': convert_html,
}

# Также обрабатываем .fb2.zip
FB2_ZIP_PATTERN = '.fb2.zip'

# Описания форматов для отображения
FORMAT_DESCRIPTIONS = {
    '.epub': 'EPUB',
    '.fb2': 'FB2',
    '.pdf': 'PDF',
    '.docx': 'DOCX',
    '.mobi': 'MOBI',
    '.azw3': 'AZW3',
    '.azw': 'AZW',
    '.rtf': 'RTF',
    '.html': 'HTML',
    '.htm': 'HTM',
}


class BookToTextApp(ctk.CTk, TkinterDnD.DnDWrapper):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        # Настройки окна (Liquid Glass дизайн)
        self.title("BookToText — Конвертер книг в текст")
        self.geometry("820x820")
        self.minsize(720, 750)
        ctk.set_appearance_mode("dark")
        
        self.configure(fg_color="#121213")

        self.file_queue: list[str] = []
        self._is_converting = False
        self._conversion_log: list[str] = []
        self.cancel_event = threading.Event()

        self._build_ui()

    def _build_ui(self):
        """Построение интерфейса в стиле Liquid Glass."""

        # === Основной контейнер ===
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=20)

        # === Заголовок ===
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        header = ctk.CTkLabel(
            header_frame,
            text="BookToText",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color="#FFFFFF",
        )
        header.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Конвертер электронных книг и документов в чистый текст (.txt, UTF-8)",
            font=ctk.CTkFont(size=14),
            text_color="#8E8E93",
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        formats_label = ctk.CTkLabel(
            header_frame,
            text="Форматы:  EPUB  •  FB2  •  PDF  •  DOCX  •  MOBI/AZW3  •  RTF  •  HTML",
            font=ctk.CTkFont(size=12),
            text_color="#636366",
        )
        formats_label.pack(anchor="w", pady=(4, 0))

        # === Drag & Drop Area ===
        self.dnd_frame = ctk.CTkFrame(
            main_frame, 
            fg_color="#1C1C1E", 
            corner_radius=16,
            border_width=1,
            border_color="#3A3A3C"
        )
        self.dnd_frame.pack(fill="x", pady=(0, 15), ipady=15)
        
        self.dnd_label = ctk.CTkLabel(
            self.dnd_frame,
            text="Перетащите файлы или папки сюда",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#8E8E93"
        )
        self.dnd_label.pack(expand=True, pady=25)

        self.dnd_frame.drop_target_register(DND_FILES)
        self.dnd_frame.dnd_bind('<<Drop>>', self._on_drop)
        self.dnd_frame.dnd_bind('<<DragEnter>>', self._on_drag_enter)
        self.dnd_frame.dnd_bind('<<DragLeave>>', self._on_drag_leave)

        self.dnd_label.drop_target_register(DND_FILES)
        self.dnd_label.dnd_bind('<<Drop>>', self._on_drop)

        # === Кнопки выбора ===
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 15))

        self.btn_files = ctk.CTkButton(
            btn_frame,
            text="Выбрать файлы",
            command=self._select_files,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2C2C2E",
            hover_color="#3A3A3C",
            text_color="#FFFFFF",
            corner_radius=10,
        )
        self.btn_files.pack(side="left", padx=(0, 10))

        self.btn_folder = ctk.CTkButton(
            btn_frame,
            text="Выбрать папку",
            command=self._select_folder,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2C2C2E",
            hover_color="#3A3A3C",
            text_color="#FFFFFF",
            corner_radius=10,
        )
        self.btn_folder.pack(side="left", padx=(0, 10))

        self.btn_clear = ctk.CTkButton(
            btn_frame,
            text="Очистить",
            command=self._clear_queue,
            width=120,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=1,
            border_color="#48484A",
            hover_color="#3A3A3C",
            text_color="#FF453A",
            corner_radius=10,
        )
        self.btn_clear.pack(side="left")

        self.file_count_label = ctk.CTkLabel(
            btn_frame,
            text="0 файлов",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#8E8E93",
        )
        self.file_count_label.pack(side="right", padx=(10, 0))

        # === Очередь файлов ===
        self.queue_text = ctk.CTkTextbox(
            main_frame,
            height=160,
            font=ctk.CTkFont(family="Menlo", size=13),
            state="disabled",
            wrap="none",
            corner_radius=12,
            fg_color="#1C1C1E",
            border_width=1,
            border_color="#333336",
            text_color="#E5E5EA"
        )
        self.queue_text.pack(fill="both", expand=True, pady=(0, 15))

        # === Панель опций ===
        options_frame = ctk.CTkFrame(
            main_frame,
            fg_color="#1C1C1E",
            corner_radius=12,
            border_width=1,
            border_color="#2C2C2E"
        )
        options_frame.pack(fill="x", pady=(0, 15), ipady=8)

        format_label = ctk.CTkLabel(
            options_frame,
            text="Формат сохранения:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#8E8E93"
        )
        format_label.pack(side="left", padx=(15, 10))

        self.format_var = ctk.StringVar(value="txt")
        self.format_btn = ctk.CTkSegmentedButton(
            options_frame,
            values=["txt", "md"],
            variable=self.format_var,
            width=120,
            height=32,
            fg_color="#2C2C2E",
            selected_color="#0A84FF",
            selected_hover_color="#007AFF",
            text_color="#FFFFFF"
        )
        self.format_btn.pack(side="left", padx=(0, 20))

        self.rename_var = ctk.BooleanVar(value=True)
        self.rename_cb = ctk.CTkCheckBox(
            options_frame,
            text="Умное переименование (Автор - Название)",
            variable=self.rename_var,
            font=ctk.CTkFont(size=13),
            text_color="#E5E5EA",
            fg_color="#0A84FF",
            hover_color="#007AFF",
            border_color="#8E8E93"
        )
        self.rename_cb.pack(side="left", padx=(20, 15))

        # === Папка сохранения ===
        save_frame = ctk.CTkFrame(
            main_frame,
            fg_color="#1C1C1E",
            corner_radius=12,
            border_width=1,
            border_color="#2C2C2E"
        )
        save_frame.pack(fill="x", pady=(0, 15), ipady=8)

        self.save_to_source_var = ctk.BooleanVar(value=True)
        self.save_mode_cb = ctk.CTkCheckBox(
            save_frame,
            text="Сохранять в папку исходного файла",
            variable=self.save_to_source_var,
            command=self._toggle_save_mode,
            font=ctk.CTkFont(size=13),
            text_color="#E5E5EA",
            fg_color="#0A84FF",
            hover_color="#007AFF",
            border_color="#8E8E93"
        )
        self.save_mode_cb.pack(side="left", padx=(15, 20))

        self.custom_save_dir = ""
        self.btn_select_save_dir = ctk.CTkButton(
            save_frame,
            text="Выбрать папку...",
            command=self._select_save_dir,
            state="disabled",
            width=130,
            height=32,
            fg_color="#2C2C2E",
            hover_color="#3A3A3C",
            text_color="#FFFFFF"
        )
        self.btn_select_save_dir.pack(side="left", padx=(0, 15))

        self.lbl_save_dir = ctk.CTkLabel(
            save_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#8E8E93"
        )
        self.lbl_save_dir.pack(side="left", fill="x", expand=True, padx=(0, 15))

        # === Прогресс-бар ===
        progress_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(5, 10))

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=8,
            corner_radius=4,
            progress_color="#0A84FF",
            fg_color="#3A3A3C"
        )
        self.progress_bar.pack(fill="x", side="left", expand=True, padx=(0, 15))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#8E8E93",
            width=40,
        )
        self.progress_label.pack(side="right")

        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Готово к работе. Перетащите файлы или выберите их вручную.",
            font=ctk.CTkFont(size=13),
            text_color="#8E8E93",
        )
        self.status_label.pack(anchor="w", pady=(0, 10))

        # === Лог ошибок ===
        self.log_text = ctk.CTkTextbox(
            main_frame,
            height=80,
            font=ctk.CTkFont(family="Menlo", size=11),
            state="disabled",
            wrap="word",
            corner_radius=12,
            fg_color="#1A1A1C",
            border_width=1,
            border_color="#2C2C2E",
            text_color="#AEAEB2"
        )
        self.log_text.pack(fill="x", pady=(0, 15))

        # === Кнопка конвертации ===
        self.btn_convert = ctk.CTkButton(
            main_frame,
            text="Конвертировать",
            command=self._start_conversion,
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#0A84FF",
            hover_color="#007AFF",
            text_color="#FFFFFF",
            corner_radius=8,
        )
        self.btn_convert.pack(fill="x", pady=(10, 0))

    def _toggle_save_mode(self):
        if self.save_to_source_var.get():
            self.btn_select_save_dir.configure(state="disabled")
            self.lbl_save_dir.configure(text="")
        else:
            self.btn_select_save_dir.configure(state="normal")
            if not self.custom_save_dir:
                self._select_save_dir()
            else:
                self.lbl_save_dir.configure(text=self.custom_save_dir)

    def _select_save_dir(self):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.custom_save_dir = folder
            self.lbl_save_dir.configure(text=folder)
        else:
            if not self.custom_save_dir:
                self.save_to_source_var.set(True)
                self._toggle_save_mode()

    def _on_drag_enter(self, event):
        """Подсветка зоны при перетаскивании."""
        self.dnd_frame.configure(border_color="#0A84FF", fg_color="#2C2C2E")
        self.dnd_label.configure(text_color="#0A84FF")

    def _on_drag_leave(self, event):
        """Возврат цвета при уходе курсора."""
        self.dnd_frame.configure(border_color="#3A3A3C", fg_color="#1C1C1E")
        self.dnd_label.configure(text_color="#8E8E93")

    def _on_drop(self, event):
        """Обработка сброшенных файлов."""
        self._on_drag_leave(event)
        if event.data:
            # Разбиваем строку путей через Tcl list parser (поддержка пробелов)
            paths = self.tk.splitlist(event.data)
            valid_paths = []
            all_exts = set(SUPPORTED_EXTENSIONS.keys())
            for path in paths:
                if os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        for fname in files:
                            fpath = os.path.join(root, fname)
                            flow = fname.lower()
                            if flow.endswith(FB2_ZIP_PATTERN) or os.path.splitext(flow)[1] in all_exts:
                                valid_paths.append(fpath)
                else:
                    flow = path.lower()
                    if flow.endswith(FB2_ZIP_PATTERN) or os.path.splitext(flow)[1] in all_exts:
                        valid_paths.append(path)
            
            if valid_paths:
                self._add_to_queue(valid_paths)
            else:
                self._set_status("В перетащенных данных нет поддерживаемых файлов.")

    # ─── Выбор файлов ───
    def _select_files(self):
        """Диалог выбора файлов."""
        filetypes = [
            ("Книги и документы",
             "*.epub *.fb2 *.pdf *.docx *.mobi *.azw3 *.azw *.rtf *.html *.htm"),
            ("FB2 ZIP", "*.fb2.zip *.zip"),
            ("Все файлы", "*.*"),
        ]
        paths = filedialog.askopenfilenames(
            title="Выберите файлы для конвертации",
            filetypes=filetypes,
        )
        if paths:
            self._add_to_queue(list(paths))

    def _select_folder(self):
        """Диалог выбора папки — сканирует все поддерживаемые файлы рекурсивно."""
        folder = filedialog.askdirectory(title="Выберите папку с файлами")
        if not folder:
            return
        found = []
        all_exts = set(SUPPORTED_EXTENSIONS.keys())
        for root, dirs, files in os.walk(folder):
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                flow = fname.lower()
                if flow.endswith(FB2_ZIP_PATTERN):
                    found.append(fpath)
                    continue
                ext = os.path.splitext(flow)[1]
                if ext in all_exts:
                    found.append(fpath)
        if found:
            self._add_to_queue(found)
        else:
            self._set_status("В выбранной папке не найдено поддерживаемых файлов.")

    def _add_to_queue(self, paths: list[str]):
        """Добавление файлов в очередь без дублей."""
        existing = set(self.file_queue)
        added = 0
        for p in paths:
            if p not in existing:
                self.file_queue.append(p)
                existing.add(p)
                added += 1
        self._refresh_queue_view()
        self._set_status(f"Добавлено: {added}. Всего в очереди: {len(self.file_queue)}.")

    def _clear_queue(self):
        """Очистка очереди."""
        self.file_queue.clear()
        self._conversion_log.clear()
        self._refresh_queue_view()
        self._refresh_log_view()
        self.progress_bar.set(0)
        self.progress_label.configure(text="0%")
        self._set_status("Очередь очищена.")

    def _refresh_queue_view(self):
        """Обновление текстового поля с очередью."""
        self.queue_text.configure(state="normal")
        self.queue_text.delete("1.0", END)
        for i, path in enumerate(self.file_queue, 1):
            basename = os.path.basename(path)
            ext = self._get_format_label(path)
            self.queue_text.insert(END, f"  {i:>3}.  [{ext:>5}]  {basename}\n")
        self.queue_text.configure(state="disabled")
        count = len(self.file_queue)
        # Правильное склонение
        if count % 10 == 1 and count % 100 != 11:
            word = "файл"
        elif count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
            word = "файла"
        else:
            word = "файлов"
        self.file_count_label.configure(text=f"{count} {word}")

    def _refresh_log_view(self):
        """Обновление лога обработки."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", END)
        for entry in self._conversion_log:
            self.log_text.insert(END, entry + "\n")
        self.log_text.see(END)
        self.log_text.configure(state="disabled")

    def _add_log_entry(self, entry: str):
        """Добавление записи в лог (потокобезопасно — вызывать через self.after)."""
        self._conversion_log.append(entry)
        self.log_text.configure(state="normal")
        self.log_text.insert(END, entry + "\n")
        self.log_text.see(END)
        self.log_text.configure(state="disabled")

    def _set_status(self, text: str):
        """Обновление строки статуса."""
        self.status_label.configure(text=text)

    @staticmethod
    def _get_format_label(file_path: str) -> str:
        """Получение метки формата для отображения."""
        lower = file_path.lower()
        if lower.endswith('.fb2.zip'):
            return 'FB2Z'
        ext = os.path.splitext(lower)[1]
        return FORMAT_DESCRIPTIONS.get(ext, ext.upper().lstrip('.'))

    # ─── Конвертация ───
    def _start_conversion(self):
        """Запуск конвертации в пуле потоков или отмена."""
        if self._is_converting:
            self.cancel_event.set()
            self.btn_convert.configure(state="disabled", text="Отменяем...")
            return
            
        if not self.file_queue:
            self._set_status("Очередь пуста — добавьте файлы.")
            return
            
        self._is_converting = True
        self.cancel_event.clear()
        self._conversion_log.clear()
        self._refresh_log_view()
        
        self.btn_convert.configure(text="Отмена", fg_color="#FF3B30", hover_color="#FF453A")
        self.btn_files.configure(state="disabled")
        self.btn_folder.configure(state="disabled")
        self.btn_clear.configure(state="disabled")
        
        thread = threading.Thread(target=self._conversion_master, daemon=True)
        thread.start()

    def _conversion_master(self):
        """Управляющий поток для пула конвертации."""
        total = len(self.file_queue)
        self.success_count = 0
        self.error_count = 0
        self.processed_count = 0
        
        format_mode = self.format_var.get()
        use_smart_rename = self.rename_var.get()
        ext = f".{format_mode}"
        save_dir = None if self.save_to_source_var.get() else self.custom_save_dir

        workers = max(1, os.cpu_count() - 1) if os.cpu_count() else 4
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._process_single_file, idx, file_path, format_mode, use_smart_rename, ext, save_dir): idx
                for idx, file_path in enumerate(self.file_queue)
            }
            
            for future in concurrent.futures.as_completed(futures):
                idx = futures[future]
                try:
                    res = future.result()
                    if res:
                        self.success_count += 1
                except InterruptedError:
                    pass
                except Exception as e:
                    self.error_count += 1
                
                self.processed_count += 1
                progress = self.processed_count / total
                percent_text = f"{int(progress * 100)}%"
                self.after(0, self.progress_bar.set, progress)
                self.after(0, self.progress_label.configure, {"text": percent_text})
                
                if self.cancel_event.is_set():
                    # При отмене прекращаем обработку новых задач
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

        if not self.cancel_event.is_set():
            self.after(0, self.progress_bar.set, 1.0)
            self.after(0, self.progress_label.configure, {"text": "100%"})

        if self.cancel_event.is_set():
            final_msg = f"Отменено. Успешно: {self.success_count}, ошибок: {self.error_count} из {total}."
        elif self.error_count == 0:
            final_msg = f"Готово! Все {self.success_count} файл(ов) успешно конвертированы."
        else:
            final_msg = f"Завершено. Успешно: {self.success_count}, ошибок: {self.error_count} из {total}."
            
        self.after(0, self._set_status, final_msg)
        self.after(0, self._conversion_done)

    def _process_single_file(self, idx: int, file_path: str, format_mode: str, use_smart_rename: bool, ext: str, save_dir: str):
        """Задача для рабочего потока в пуле."""
        if self.cancel_event.is_set():
            raise InterruptedError()
            
        basename = os.path.basename(file_path)
        self.after(0, self._set_status, f"[{self.processed_count+1}/{len(self.file_queue)}] Обработка: {basename}")

        try:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            if not os.access(file_path, os.R_OK):
                raise PermissionError(f"Нет доступа для чтения: {file_path}")
                
            out_dir = save_dir if save_dir else os.path.dirname(file_path)
            if not os.path.exists(out_dir):
                raise FileNotFoundError(f"Папка сохранения не существует: {out_dir}")
            if not os.access(out_dir, os.W_OK):
                raise PermissionError(f"Нет доступа для записи в папку: {out_dir}")

            converter = self._get_converter(file_path)
            if converter is None:
                raise ValueError(f"Формат не поддерживается: {basename}")

            author, title = None, None
            if use_smart_rename:
                self.after(0, self._set_status, f"[{self.processed_count+1}/{len(self.file_queue)}] Метаданные: {basename}")
                author, title = extract_metadata(file_path)

            if self.cancel_event.is_set():
                raise InterruptedError()

            self.after(0, self._set_status, f"[{self.processed_count+1}/{len(self.file_queue)}] Конвертация: {basename}")
            raw_text = converter(file_path, format_mode=format_mode, cancel_event=self.cancel_event)
            
            if self.cancel_event.is_set():
                raise InterruptedError()
                
            cleaned = clean_text(raw_text)

            save_path = safe_save_path(file_path, author=author, title=title, ext=ext, out_dir=out_dir)
            with open(save_path, 'w', encoding='utf-8') as out:
                out.write(cleaned)

            source_size = os.path.getsize(file_path)
            text_size = os.path.getsize(save_path)
            
            if source_size > 50 * 1024 and text_size < source_size * 0.02 and text_size < 3000:
                raise ValueError(f"Конвертация неполная (извлечено всего {text_size} байт). Возможно, повреждённая структура или DRM.")
            
            if text_size == 0:
                raise ValueError("Не удалось извлечь текст (результат пуст).")

            saved_name = os.path.basename(save_path)
            self.after(0, self._log_to_queue, idx, f"{basename} (Готово)")
            self.after(0, self._add_log_entry, f"Успех: {basename} → {saved_name}")
            return True

        except InterruptedError:
            self.after(0, self._log_to_queue, idx, f"{basename} (Отменено)")
            self.after(0, self._add_log_entry, f"Отменено: {basename}")
            raise
        except Exception as e:
            err_msg = str(e)[:150]
            self.after(0, self._log_to_queue, idx, f"{basename} (Ошибка)")
            self.after(0, self._add_log_entry, f"Ошибка: {basename}: {err_msg}")
            raise

    def _log_to_queue(self, index: int, message: str):
        """Обновление строки в текстовом поле очереди."""
        self.queue_text.configure(state="normal")
        line_start = f"{index + 1}.0"
        line_end = f"{index + 1}.end"
        self.queue_text.delete(line_start, line_end)
        ext = self._get_format_label(self.file_queue[index])
        self.queue_text.insert(line_start, f"  {index+1:>3}.  [{ext:>5}]  {message}")
        self.queue_text.configure(state="disabled")

    def _conversion_done(self):
        """Разблокировка интерфейса после завершения."""
        self._is_converting = False
        self.btn_convert.configure(state="normal", text="Конвертировать", fg_color="#0A84FF", hover_color="#007AFF")
        self.btn_files.configure(state="normal")
        self.btn_folder.configure(state="normal")
        self.btn_clear.configure(state="normal")

    @staticmethod
    def _get_converter(file_path: str):
        """Определение конвертера по расширению файла."""
        lower = file_path.lower()
        # Проверяем fb2.zip
        if lower.endswith(FB2_ZIP_PATTERN):
            return convert_fb2
        ext = os.path.splitext(lower)[1]
        return SUPPORTED_EXTENSIONS.get(ext)


def main():
    app = BookToTextApp()
    app.mainloop()


if __name__ == "__main__":
    main()
