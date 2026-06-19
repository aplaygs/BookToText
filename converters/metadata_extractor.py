import os
import re
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

IGNORED_METADATA = {
    'unknown', 'no author', 'n/a', 'none', 'unknown author', 'untitled', 
    'temp', 'placeholder', 'выпуск', 'книга', 'автор', 'без автора', 'неизвестен'
}

def sanitize_filename(name: str) -> str:
    """Очищает строку для безопасного использования в имени файла."""
    if not name:
        return ""
    # Удаляем недопустимые символы
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Удаляем спецсимволы перевода строк
    name = name.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Схлопываем лишние пробелы
    name = re.sub(r'\s+', " ", name)
    return name.strip()

def parse_metadata_from_filename(filename: str) -> tuple[str | None, str | None]:
    """Разбирает имя исходного файла для извлечения автора и названия."""
    lower = filename.lower()
    if lower.endswith('.fb2.zip'):
        basename = filename[:-8]
    else:
        basename = os.path.splitext(filename)[0]
        
    # Очищаем от мусорных тегов (например, [litres], (ru))
    basename = re.sub(r'\[.*?\]', '', basename)
    basename = re.sub(r'\(.*?\)', '', basename)
    
    # Пытаемся разбить по разделителям
    for sep in [' - ', ' — ', ' – ', ' _ ', '-', '_']:
        if sep in basename:
            parts = basename.split(sep, 1)
            author = sanitize_filename(parts[0])
            title = sanitize_filename(parts[1])
            if author and title:
                return author, title
                
    # Если разделителей нет, считаем все название книги
    title = sanitize_filename(basename)
    return None, title if title else None

def _is_valid_meta(value: str) -> bool:
    if not value:
        return False
    val_lower = value.strip().lower()
    if not val_lower or val_lower in IGNORED_METADATA:
        return False
    # Если строка состоит только из цифр и пунктуации
    if not re.search(r'[a-zA-Zа-яА-ЯёЁ]', val_lower):
        return False
    return True

def _clean_meta_value(meta_item) -> str | None:
    if isinstance(meta_item, tuple):
        val = meta_item[0]
    elif hasattr(meta_item, 'value'):
        val = meta_item.value
    elif hasattr(meta_item, 'get_content'):
        val = meta_item.get_content()
    else:
        val = str(meta_item)
        
    if isinstance(val, bytes):
        val = val.decode('utf-8', errors='replace')
        
    val = sanitize_filename(val)
    return val if _is_valid_meta(val) else None

def _extract_epub_metadata(file_path: str) -> tuple[str | None, str | None]:
    try:
        from ebooklib import epub
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            book = epub.read_epub(file_path, options={'ignore_ncx': False})
        
        titles = book.get_metadata('DC', 'title')
        title = _clean_meta_value(titles[0]) if titles else None
        
        creators = book.get_metadata('DC', 'creator')
        author = _clean_meta_value(creators[0]) if creators else None
        
        return author, title
    except Exception:
        return None, None

def _extract_fb2_metadata(file_path: str) -> tuple[str | None, str | None]:
    try:
        ext = os.path.splitext(file_path)[1].lower()
        xml_content = None
        if ext == '.zip' or file_path.lower().endswith('.fb2.zip'):
            with zipfile.ZipFile(file_path, 'r') as zf:
                for name in zf.namelist():
                    if name.lower().endswith('.fb2'):
                        xml_content = zf.read(name)
                        break
        else:
            with open(file_path, 'rb') as f:
                xml_content = f.read()
                
        if not xml_content:
            return None, None
            
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            content_str = xml_content.decode('utf-8', errors='replace')
            root = ET.fromstring(content_str.encode('utf-8'))
            
        ns = ''
        if root.tag.startswith('{'):
            ns = root.tag.split('}')[0] + '}'
            
        title_info = root.find(f'.//{ns}title-info')
        if title_info is None:
            return None, None
            
        title_node = title_info.find(f'{ns}book-title')
        title = sanitize_filename(title_node.text) if title_node is not None and title_node.text else None
        if not _is_valid_meta(title):
            title = None
        
        author_node = title_info.find(f'{ns}author')
        author = None
        if author_node is not None:
            first = author_node.find(f'{ns}first-name')
            last = author_node.find(f'{ns}last-name')
            middle = author_node.find(f'{ns}middle-name')
            
            parts = []
            if first is not None and first.text: parts.append(first.text.strip())
            if middle is not None and middle.text: parts.append(middle.text.strip())
            if last is not None and last.text: parts.append(last.text.strip())
            
            if parts:
                author_candidate = sanitize_filename(" ".join(parts))
                if _is_valid_meta(author_candidate):
                    author = author_candidate
                    
        return author, title
    except Exception:
        return None, None

def _extract_pdf_metadata(file_path: str) -> tuple[str | None, str | None]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        meta = reader.metadata
        if not meta:
            return None, None
            
        author = sanitize_filename(meta.author) if meta.author else None
        title = sanitize_filename(meta.title) if meta.title else None
        
        return (author if _is_valid_meta(author) else None, 
                title if _is_valid_meta(title) else None)
    except Exception:
        return None, None

def _extract_docx_metadata(file_path: str) -> tuple[str | None, str | None]:
    try:
        from docx import Document
        doc = Document(file_path)
        props = doc.core_properties
        
        author = sanitize_filename(props.author) if props.author else None
        title = sanitize_filename(props.title) if props.title else None
        
        return (author if _is_valid_meta(author) else None, 
                title if _is_valid_meta(title) else None)
    except Exception:
        return None, None

def _extract_html_metadata(file_path: str) -> tuple[str | None, str | None]:
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(8192) # Читаем начало для метаданных
        soup = BeautifulSoup(content, 'html.parser')
        
        title = sanitize_filename(soup.title.string) if soup.title and soup.title.string else None
        
        author_meta = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', attrs={'name': 'creator'})
        author = None
        if author_meta and author_meta.has_attr('content'):
            author = sanitize_filename(author_meta['content'])
            
        return (author if _is_valid_meta(author) else None, 
                title if _is_valid_meta(title) else None)
    except Exception:
        return None, None

def _extract_mobi_metadata(file_path: str) -> tuple[str | None, str | None]:
    # Пытаемся извлечь название из бинарного заголовка MOBI
    try:
        with open(file_path, 'rb') as f:
            data = f.read(1024)
            pdb_name = data[:31].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
            title = sanitize_filename(pdb_name)
            if _is_valid_meta(title):
                return None, title # Автор неизвестен из PDB заголовка
    except Exception:
        pass
    return None, None

def extract_metadata(file_path: str) -> tuple[str | None, str | None]:
    """
    Извлекает автора и название книги из файла.
    Если метаданные внутри не найдены или некорректны, пытается распарсить имя файла.
    """
    lower = file_path.lower()
    author, title = None, None
    
    if lower.endswith('.epub'):
        author, title = _extract_epub_metadata(file_path)
    elif lower.endswith('.fb2') or lower.endswith('.fb2.zip'):
        author, title = _extract_fb2_metadata(file_path)
    elif lower.endswith('.pdf'):
        author, title = _extract_pdf_metadata(file_path)
    elif lower.endswith('.docx'):
        author, title = _extract_docx_metadata(file_path)
    elif lower.endswith('.html') or lower.endswith('.htm'):
        author, title = _extract_html_metadata(file_path)
    elif lower.endswith('.mobi') or lower.endswith('.azw3') or lower.endswith('.azw'):
        author, title = _extract_mobi_metadata(file_path)
        
    filename = os.path.basename(file_path)
    fallback_author, fallback_title = parse_metadata_from_filename(filename)
    
    final_author = author if author else fallback_author
    final_title = title if title else fallback_title
    
    return final_author, final_title
