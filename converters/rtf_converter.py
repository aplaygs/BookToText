from striprtf.striprtf import rtf_to_text


def convert_rtf(file_path: str, format_mode: str = 'txt', cancel_event=None) -> str:
    """Конвертация RTF в текст."""
    try:
        import charset_normalizer
        with open(file_path, 'rb') as f:
            rawdata = f.read()
        best_match = charset_normalizer.from_bytes(rawdata).best()
        encoding = best_match.encoding if best_match else 'utf-8'
        rtf_content = rawdata.decode(encoding, errors='replace')
    except ImportError:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            rtf_content = f.read()
            
    if cancel_event and cancel_event.is_set():
        raise InterruptedError("Отменено пользователем")
    text = rtf_to_text(rtf_content)
    return text
