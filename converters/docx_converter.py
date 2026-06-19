from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

def iter_block_items(parent):
    """Yield each paragraph and table child within *parent*, in document order."""
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        return
        
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def convert_docx(file_path: str, format_mode: str = 'txt', cancel_event=None) -> str:
    """Конвертация DOCX в текст или Markdown."""
    doc = Document(file_path)
    texts = []
    
    for block in iter_block_items(doc):
        if cancel_event and cancel_event.is_set():
            raise InterruptedError("Отменено пользователем")
            
        if isinstance(block, Paragraph):
            paragraph = block
            style_name = paragraph.style.name if paragraph.style else ""
            para_text = ""
            
            for run in paragraph.runs:
                text = run.text
                if not text:
                    continue
                    
                if format_mode == 'md':
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
                
            if format_mode == 'md':
                if style_name.startswith('Heading'):
                    try:
                        level = int(style_name.split()[-1])
                    except (ValueError, IndexError):
                        level = 1
                    hashes = '#' * min(level, 6)
                    texts.append(f"\n{hashes} {para_text.strip()}\n")
                elif 'List Bullet' in style_name:
                    texts.append(f"- {para_text.strip()}")
                elif 'List Number' in style_name:
                    texts.append(f"1. {para_text.strip()}")
                else:
                    texts.append(para_text)
            else:
                texts.append(para_text)
                
        elif isinstance(block, Table):
            table = block
            if format_mode == 'md':
                texts.append("\n")
                for i, row in enumerate(table.rows):
                    row_data = [cell.text.replace('\n', ' ').strip() for cell in row.cells]
                    texts.append("| " + " | ".join(row_data) + " |")
                    if i == 0:
                        texts.append("|" + "|".join(["---"] * len(row.cells)) + "|")
                texts.append("\n")
            else:
                for row in table.rows:
                    row_data = [cell.text.replace('\n', ' ').strip() for cell in row.cells]
                    texts.append("\t".join(row_data))
                texts.append("\n")
            
    return '\n\n'.join(texts)

