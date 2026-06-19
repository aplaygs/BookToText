import xml.etree.ElementTree as ET
import zipfile
import os

def parse_fb2_node(node, ns, format_mode='txt', title_level=1) -> str:
    """Рекурсивный обход XML-дерева FB2 для генерации текста или Markdown."""
    tag_name = node.tag
    if tag_name.startswith('{'):
        tag_name = tag_name.split('}', 1)[1]
    
    # Рекурсивный обход детей
    if tag_name == 'p':
        text = ""
        for child in node:
            text += parse_fb2_node(child, ns, format_mode, title_level)
            if child.tail:
                text += child.tail
        if node.text:
            text = node.text + text
        text = text.strip()
        if format_mode == 'md':
            return f"\n\n{text}\n\n"
        else:
            return f"{text}\n"
    
    elif tag_name == 'strong':
        text = ""
        for child in node:
            text += parse_fb2_node(child, ns, format_mode, title_level)
            if child.tail:
                text += child.tail
        if node.text:
            text = node.text + text
        text = text.strip()
        if format_mode == 'md':
            return f"**{text}**"
        return text

    elif tag_name == 'emphasis':
        text = ""
        for child in node:
            text += parse_fb2_node(child, ns, format_mode, title_level)
            if child.tail:
                text += child.tail
        if node.text:
            text = node.text + text
        text = text.strip()
        if format_mode == 'md':
            return f"*{text}*"
        return text
    
    elif tag_name == 'title':
        text = ""
        for child in node:
            text += parse_fb2_node(child, ns, format_mode, title_level)
            if child.tail:
                text += child.tail
        if node.text:
            text = node.text + text
        text = text.strip()
        if format_mode == 'md':
            hashes = '#' * min(title_level, 6)
            return f"\n\n{hashes} {text}\n\n"
        else:
            return f"\n{text}\n"

    elif tag_name == 'subtitle':
        text = ""
        for child in node:
            text += parse_fb2_node(child, ns, format_mode, title_level)
            if child.tail:
                text += child.tail
        if node.text:
            text = node.text + text
        text = text.strip()
        if format_mode == 'md':
            hashes = '#' * min(title_level + 1, 6)
            return f"\n\n{hashes} {text}\n\n"
        else:
            return f"\n{text}\n"

    elif tag_name == 'section':
        texts = []
        for child in node:
            child_text = parse_fb2_node(child, ns, format_mode, title_level + 1)
            if child_text:
                texts.append(child_text)
            if child.tail and child.tail.strip():
                texts.append(child.tail.strip())
        return "".join(texts)

    elif tag_name == 'epigraph':
        text = ""
        for child in node:
            text += parse_fb2_node(child, ns, format_mode, title_level)
            if child.tail:
                text += child.tail
        if node.text:
            text = node.text + text
        text = text.strip()
        if format_mode == 'md':
            lines = text.split('\n')
            quoted = [f"> {line}" for line in lines if line.strip()]
            return f"\n\n" + "\n".join(quoted) + "\n\n"
        return f"\n{text}\n"

    elif tag_name in ('poem', 'cite'):
        texts = []
        for child in node:
            child_text = parse_fb2_node(child, ns, format_mode, title_level)
            if child_text:
                texts.append(child_text)
            if child.tail and child.tail.strip():
                texts.append(child.tail.strip())
        text = "".join(texts)
        if format_mode == 'md':
            lines = text.split('\n')
            quoted = [f"> {line}" for line in lines if line.strip()]
            return f"\n\n" + "\n".join(quoted) + "\n\n"
        return f"\n{text}\n"

    elif tag_name == 'stanza':
        texts = []
        for child in node:
            child_text = parse_fb2_node(child, ns, format_mode, title_level)
            if child_text:
                texts.append(child_text)
            if child.tail and child.tail.strip():
                texts.append(child.tail.strip())
        return "\n".join(texts) + "\n\n"

    elif tag_name == 'v':
        text = ""
        for child in node:
            text += parse_fb2_node(child, ns, format_mode, title_level)
            if child.tail:
                text += child.tail
        if node.text:
            text = node.text + text
        text = text.strip()
        return f"{text}\n"

    # Обработка других тегов (body, empty-line, poem и т.д.)
    texts = []
    if node.text and node.text.strip():
        texts.append(node.text)
    for child in node:
        child_text = parse_fb2_node(child, ns, format_mode, title_level)
        if child_text:
            texts.append(child_text)
        if child.tail and child.tail.strip():
            texts.append(child.tail)
    
    return "".join(texts)


def _parse_fb2_content(xml_content: bytes, format_mode: str = 'txt', cancel_event=None) -> str:
    """Парсинг содержимого FB2 XML."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        content_str = xml_content.decode('utf-8', errors='replace')
        root = ET.fromstring(content_str.encode('utf-8'))
    
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'
    
    texts = []
    # Извлекаем текст только из элементов body (пропуская description/метаданные)
    for body in root.iter(f'{ns}body'):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Отменено пользователем")
        body_text = parse_fb2_node(body, ns, format_mode, title_level=1)
        if body_text.strip():
            texts.append(body_text.strip())
    
    if not texts:
        # Fallback: извлекаем весь текст из body как плоский
        for body in root.iter(f'{ns}body'):
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Отменено пользователем")
            body_text = ''.join(body.itertext()).strip()
            if body_text:
                texts.append(body_text)
    
    return '\n\n'.join(texts)


def convert_fb2(file_path: str, format_mode: str = 'txt', cancel_event=None) -> str:
    """Конвертация FB2 или FB2.ZIP в текст или Markdown."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.zip' or file_path.lower().endswith('.fb2.zip'):
        with zipfile.ZipFile(file_path, 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith('.fb2'):
                    content = zf.read(name)
                    return _parse_fb2_content(content, format_mode, cancel_event)
        raise ValueError("Архив не содержит файлов .fb2")
    else:
        with open(file_path, 'rb') as f:
            content = f.read()
        return _parse_fb2_content(content, format_mode, cancel_event)
