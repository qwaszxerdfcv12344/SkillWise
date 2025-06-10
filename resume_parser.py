# resume_parser.py
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from PIL import Image


def parse_resume(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
        if not text.strip():  # fallback to OCR
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img)
    return text.strip()

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
    return text

def parse_resume(resume_path):
    text = extract_text_from_pdf(resume_path)
    if len(text.strip()) < 100:  # fallback if text extraction fails
        text = extract_text_with_ocr(resume_path)
    return text