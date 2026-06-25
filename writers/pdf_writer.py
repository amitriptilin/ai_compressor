import os
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

def save_as_pdf(text: str, output_path: str) -> None:
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    
    styles = getSampleStyleSheet()
    font_path = _find_cyrillic_font()
    
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
            font_name = 'CyrillicFont'
        except Exception as e:
            logger.warning(f"Не удалось зарегистрировать шрифт {font_path}: {e}")
            font_name = 'Helvetica'
    else:
        font_name = 'Helvetica'
        logger.warning("Шрифт с кириллицей не найден, используем Helvetica (русские буквы могут не отображаться)")
    
    custom_style = ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=16,
        spaceAfter=10
    )
    
    clean_text = text.replace("**", "").replace("__", "")
    paragraphs = clean_text.split("\n")
    for p in paragraphs:
        p = p.strip()
        if p:
            story.append(Paragraph(p, custom_style))
    
    doc.build(story)
    logger.info(f"Сохранено в PDF: {output_path}")

def _find_cyrillic_font() -> str | None:
    win_fonts = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\times.ttf",
        "C:\\Windows\\Fonts\\calibri.ttf"
    ]
    for f in win_fonts:
        if os.path.exists(f):
            return f
    
    linux_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf"
    ]
    for f in linux_fonts:
        if os.path.exists(f):
            return f
    
    mac_fonts = [
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttf"
    ]
    for f in mac_fonts:
        if os.path.exists(f):
            return f
    
    return None