from docx import Document


def convert_docx(file_path: str) -> str:
    """Конвертация DOCX в текст."""
    doc = Document(file_path)
    texts = []
    for paragraph in doc.paragraphs:
        texts.append(paragraph.text)
    return '\n'.join(texts)
