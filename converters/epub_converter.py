import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def convert_epub(file_path: str) -> str:
    """Конвертация EPUB в текст с сохранением порядка глав."""
    book = epub.read_epub(file_path, options={'ignore_ncx': False})
    texts = []
    
    # Получаем элементы spine для правильного порядка
    spine_ids = [item_id for item_id, _ in book.spine]
    items_by_id = {item.get_id(): item for item in book.get_items()}
    processed_ids = set()
    
    # Сначала читаем документы из spine в нужном порядке
    for item_id in spine_ids:
        item = items_by_id.get(item_id)
        if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
            # Используем html.parser вместо lxml для устойчивости к битой разметке
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            # Удаляем скрипты и стили
            for tag in soup(['script', 'style', 'link', 'meta']):
                tag.decompose()
            text = soup.get_text(separator='\n')
            if text.strip():
                texts.append(text)
            processed_ids.add(item_id)
            
    # Дополнительно проверяем, нет ли других текстовых документов вне spine
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        item_id = item.get_id()
        if item_id not in processed_ids:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            for tag in soup(['script', 'style', 'link', 'meta']):
                tag.decompose()
            text = soup.get_text(separator='\n')
            if text.strip():
                texts.append(text)
                
    return '\n\n'.join(texts)
