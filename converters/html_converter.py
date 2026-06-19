from bs4 import BeautifulSoup


def convert_html(file_path: str) -> str:
    """Конвертация HTML/HTM в чистый текст. Удаление JS, CSS и тегов."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Удаляем скрипты, стили и мета-теги
    for tag in soup(['script', 'style', 'link', 'meta', 'noscript', 'iframe']):
        tag.decompose()
    
    text = soup.get_text(separator='\n')
    return text
