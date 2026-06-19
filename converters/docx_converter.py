from docx import Document


def convert_docx(file_path: str, format_mode: str = 'txt') -> str:
    """Конвертация DOCX в текст или Markdown."""
    doc = Document(file_path)
    texts = []
    
    for paragraph in doc.paragraphs:
        style_name = paragraph.style.name if paragraph.style else ""
        para_text = ""
        
        for run in paragraph.runs:
            text = run.text
            if not text:
                continue
                
            if format_mode == 'md':
                # Простейшая поддержка жирного и курсива
                if run.bold and run.italic:
                    para_text += f"***{text}***"
                elif run.bold:
                    para_text += f"**{text}**"
                elif run.italic:
                    para_text += f"*{text}*"
                else:
                    para_text += text
            else:
                para_text += text
                
        if not para_text.strip():
            continue
            
        if format_mode == 'md' and style_name.startswith('Heading'):
            try:
                level = int(style_name.split()[-1])
            except (ValueError, IndexError):
                level = 1
            hashes = '#' * min(level, 6)
            texts.append(f"{hashes} {para_text.strip()}")
        else:
            texts.append(para_text)
            
    return '\n\n'.join(texts)
