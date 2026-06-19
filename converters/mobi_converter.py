import mobi
import tempfile
import os
from bs4 import BeautifulSoup


def convert_mobi(file_path: str) -> str:
    """Конвертация MOBI/AZW3 в текст (только незащищённые DRM книги)."""
    # mobi.extract() распаковывает во временную директорию
    with tempfile.TemporaryDirectory() as tmpdir:
        tempdir, extracted_file = mobi.extract(file_path)
        
        if not extracted_file or not os.path.exists(extracted_file):
            raise ValueError("Не удалось извлечь содержимое MOBI/AZW3. Возможно, файл защищён DRM.")
        
        with open(extracted_file, 'rb') as f:
            content = f.read()
        
        # Пробуем распарсить как HTML
        try:
            soup = BeautifulSoup(content, 'html.parser')
            for tag in soup(['script', 'style', 'link', 'meta']):
                tag.decompose()
            text = soup.get_text(separator='\n')
        except Exception:
            text = content.decode('utf-8', errors='replace')
        
        return text
