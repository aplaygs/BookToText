#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Утилиты очистки текста и безопасного сохранения для BookToText."""

import re
import os


def clean_text(text: str) -> str:
    """Очистка текста: удаление битых символов, дублей пустых строк, концевых пробелов."""
    if not text:
        return ""
    # Заменяем битые символы (не-Unicode)
    text = text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    # Удаляем нулевые байты
    text = text.replace('\x00', '')
    # Удаляем управляющие символы кроме \n, \r, \t
    text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Нормализуем переводы строк (\r\n → \n)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Удаляем концевые пробелы на каждой строке
    lines = [line.rstrip() for line in text.splitlines()]
    # Удаляем дублирующиеся пустые строки (максимум 2 подряд)
    cleaned_lines = []
    empty_count = 0
    for line in lines:
        if line == '':
            empty_count += 1
            if empty_count <= 2:
                cleaned_lines.append(line)
        else:
            empty_count = 0
            cleaned_lines.append(line)
    result = '\n'.join(cleaned_lines).strip()
    if result:
        result += '\n'
    return result


def safe_save_path(original_path: str) -> str:
    """Генерирует путь для сохранения .txt файла.

    Если файл существует — добавляет _1, _2 и т.д.
    Корректно обрабатывает двойные расширения (.fb2.zip).
    """
    directory = os.path.dirname(original_path)
    filename = os.path.basename(original_path)

    # Обработка двойного расширения .fb2.zip
    lower = filename.lower()
    if lower.endswith('.fb2.zip'):
        basename = filename[:-len('.fb2.zip')]
    else:
        basename = os.path.splitext(filename)[0]

    txt_path = os.path.join(directory, f"{basename}.txt")
    if not os.path.exists(txt_path):
        return txt_path
    index = 1
    while True:
        txt_path = os.path.join(directory, f"{basename}_{index}.txt")
        if not os.path.exists(txt_path):
            return txt_path
        index += 1
