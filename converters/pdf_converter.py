import re
from pypdf import PdfReader


def clean_pdf_hyphens(text: str) -> str:
    """Удаляет разрывы слов с переносами в конце строк."""
    return re.sub(r'([а-яА-Яa-zA-Z])-\n([а-яА-Яa-zA-Z])', r'\1\2', text)


def convert_pdf(file_path: str, format_mode: str = 'txt', cancel_event=None) -> str:
    """Конвертация PDF в текст. Постраничная обработка для экономии памяти."""
    reader = PdfReader(file_path)
    texts = []
    total_pages = len(reader.pages)
    
    for i in range(total_pages):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Отменено пользователем")
            
        page = reader.pages[i]
        page_text = page.extract_text()
        if page_text:
            cleaned = clean_pdf_hyphens(page_text)
            texts.append(cleaned.strip())
    
    return '\n\n'.join(texts)

