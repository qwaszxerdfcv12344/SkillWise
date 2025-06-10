import fitz  # PyMuPDF
from PIL import Image
import pytesseract

def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_text_with_ocr(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text += pytesseract.image_to_string(img)
    doc.close()
    return text

def parse_resume(pdf_path):
    try:
        text = extract_text_from_pdf(pdf_path)
        if len(text.strip()) < 100:  # Fallback to OCR if text extraction yields insufficient content
            text = extract_text_with_ocr(pdf_path)
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to parse resume: {str(e)}")