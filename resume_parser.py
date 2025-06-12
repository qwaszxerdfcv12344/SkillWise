import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import os
import tempfile

def is_valid_pdf(file_path):
    """Check if file is a valid PDF."""
    try:
        # Try using python-magic if available
        import magic
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        return file_type == 'application/pdf'
    except ImportError:
        # Fallback: Check file extension and try to open with PyMuPDF
        if not file_path.lower().endswith('.pdf'):
            return False
        try:
            doc = fitz.open(file_path)
            doc.close()
            return True
        except:
            return False
    except Exception:
        return False

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def extract_text_with_ocr(pdf_path):
    """Extract text from PDF using OCR."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img)
        doc.close()
        return text
    except Exception as e:
        raise Exception(f"Failed to perform OCR: {str(e)}")

def parse_resume(pdf_path):
    """Parse resume with improved error handling and validation."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume file not found: {pdf_path}")
    
    if not is_valid_pdf(pdf_path):
        raise ValueError("Invalid PDF file format")
    
    try:
        # First attempt: Direct text extraction
        text = extract_text_from_pdf(pdf_path)
        
        # If text extraction yields insufficient content, try OCR
        if len(text.strip()) < 100:
            text = extract_text_with_ocr(pdf_path)
            
        # Validate extracted text
        if not text.strip():
            raise ValueError("No text could be extracted from the resume")
            
        return text.strip()
        
    except Exception as e:
        raise Exception(f"Failed to parse resume: {str(e)}")
    finally:
        # Cleanup if file was created in temp directory
        if os.path.dirname(pdf_path) == tempfile.gettempdir():
            try:
                os.remove(pdf_path)
            except:
                pass