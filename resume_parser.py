import pytesseract
from pdf2image import convert_from_path
import tempfile
import os

def parse_resume(pdf_path):
    try:
        # Check if Tesseract is installed
        pytesseract.get_tesseract_version()  # This will raise an error if Tesseract is not found
    except pytesseract.TesseractNotFoundError:
        raise Exception("Tesseract is not installed or it's not in your PATH. Please install Tesseract OCR to parse resumes.")

    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        # Extract text from each page
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to parse resume: {str(e)}")
    finally:
        # Clean up temporary files if needed
        if os.path.exists(pdf_path):
            os.remove(pdf_path)