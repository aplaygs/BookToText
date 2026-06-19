from striprtf.striprtf import rtf_to_text


def convert_rtf(file_path: str) -> str:
    """Конвертация RTF в текст."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        rtf_content = f.read()
    text = rtf_to_text(rtf_content)
    return text
