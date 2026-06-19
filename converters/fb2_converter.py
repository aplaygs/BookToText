import xml.etree.ElementTree as ET
import zipfile
import os


def _parse_fb2_content(xml_content: bytes) -> str:
    """Парсинг содержимого FB2 XML."""
    # Определяем namespace
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        # Попытка с очисткой
        content_str = xml_content.decode('utf-8', errors='replace')
        root = ET.fromstring(content_str.encode('utf-8'))
    
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'
    
    texts = []
    # Ищем все body элементы
    for body in root.iter(f'{ns}body'):
        for section in body.iter(f'{ns}section'):
            section_texts = []
            for p in section.iter(f'{ns}p'):
                para_text = ''.join(p.itertext()).strip()
                if para_text:
                    section_texts.append(para_text)
            if section_texts:
                texts.append('\n'.join(section_texts))
    
    if not texts:
        # Fallback: извлекаем весь текст из body
        for body in root.iter(f'{ns}body'):
            body_text = ''.join(body.itertext()).strip()
            if body_text:
                texts.append(body_text)
    
    return '\n\n'.join(texts)


def convert_fb2(file_path: str) -> str:
    """Конвертация FB2 или FB2.ZIP в текст."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.zip' or file_path.lower().endswith('.fb2.zip'):
        with zipfile.ZipFile(file_path, 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith('.fb2'):
                    content = zf.read(name)
                    return _parse_fb2_content(content)
        raise ValueError("Архив не содержит файлов .fb2")
    else:
        with open(file_path, 'rb') as f:
            content = f.read()
        return _parse_fb2_content(content)
