from bs4 import BeautifulSoup, NavigableString

def html_to_markdown(tag) -> str:
    """Рекурсивно конвертирует BeautifulSoup tag в строку Markdown."""
    if tag is None:
        return ""
    
    if isinstance(tag, NavigableString):
        return str(tag).replace('\r\n', '\n')
        
    name = tag.name
    if not name:
        return ""
        
    if name in ['script', 'style', 'link', 'meta', 'noscript', 'iframe']:
        return ""
        
    children_texts = []
    for child in tag.children:
        children_texts.append(html_to_markdown(child))
    children_text = "".join(children_texts)
    
    if name == 'p':
        return f"\n\n{children_text.strip()}\n\n"
    elif name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        level = int(name[1])
        hashes = '#' * level
        return f"\n\n{hashes} {children_text.strip()}\n\n"
    elif name in ['strong', 'b']:
        text = children_text.strip()
        return f"**{text}**" if text else ""
    elif name in ['em', 'i']:
        text = children_text.strip()
        return f"*{text}*" if text else ""
    elif name == 'br':
        return "\n"
    elif name == 'li':
        return f"\n- {children_text.strip()}"
    elif name in ['ul', 'ol']:
        return f"\n{children_text}\n"
    elif name == 'blockquote':
        lines = children_text.strip().split('\n')
        quoted = [f"> {line}" for line in lines]
        return f"\n\n" + "\n".join(quoted) + "\n\n"
        
    return children_text


def convert_html(file_path: str, format_mode: str = 'txt') -> str:
    """Конвертация HTML/HTM в чистый текст или Markdown."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    if format_mode == 'md':
        body = soup.body if soup.body else soup
        text = html_to_markdown(body)
    else:
        # Режим txt (удаляем лишние теги и извлекаем текст)
        for tag in soup(['script', 'style', 'link', 'meta', 'noscript', 'iframe']):
            tag.decompose()
        text = soup.get_text(separator='\n')
        
    return text
