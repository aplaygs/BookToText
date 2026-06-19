from pypdf import PdfReader


def convert_pdf(file_path: str) -> str:
    """Конвертация PDF в текст. Постраничная обработка для экономии памяти."""
    reader = PdfReader(file_path)
    texts = []
    total_pages = len(reader.pages)
    
    for i in range(total_pages):
        page = reader.pages[i]
        page_text = page.extract_text()
        if page_text:
            texts.append(page_text.strip())
    
    return '\n\n'.join(texts)
