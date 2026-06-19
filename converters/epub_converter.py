import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from .html_converter import html_to_markdown


def convert_epub(file_path: str, format_mode: str = 'txt') -> str:
    """Конвертация EPUB в текст или Markdown с сохранением порядка глав."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        book = epub.read_epub(file_path, options={'ignore_ncx': False})
    
    texts = []
    
    # Получаем элементы spine для правильного порядка
    spine_ids = [item_id for item_id, _ in book.spine]
    items_by_id = {item.get_id(): item for item in book.get_items()}
    processed_ids = set()
    
    def process_item(item):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        if format_mode == 'md':
            body = soup.body if soup.body else soup
            text = html_to_markdown(body)
        else:
            for tag in soup(['script', 'style', 'link', 'meta']):
                tag.decompose()
            text = soup.get_text(separator='\n')
        
        if text.strip():
            texts.append(text)
            
    # Сначала читаем документы из spine в нужном порядке
    for item_id in spine_ids:
        item = items_by_id.get(item_id)
        if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
            process_item(item)
            processed_ids.add(item_id)
            
    # Дополнительно проверяем, нет ли других текстовых документов вне spine
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        item_id = item.get_id()
        if item_id not in processed_ids:
            process_item(item)
                
    return '\n\n'.join(texts)
