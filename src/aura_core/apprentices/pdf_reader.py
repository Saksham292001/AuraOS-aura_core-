# src/aura_core/apprentices/pdf_reader.py
import os
import fitz  # PyMuPDF
import pytesseract # For OCR
from PIL import Image
import io
import traceback
from typing import List

def parse_page_range(page_input, max_pages):
    """Parses a string like "1, 3-5" into a list of 0-based indices."""
    if not page_input:
        return range(max_pages) # All pages
    
    indices = set()
    try:
        parts = str(page_input).split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                start_idx = int(start.strip()) - 1
                end_idx = int(end.strip()) - 1
                if start_idx < 0 or end_idx >= max_pages or start_idx > end_idx:
                    continue # Invalid range
                for i in range(start_idx, end_idx + 1):
                    indices.add(i)
            else:
                idx = int(part.strip()) - 1
                if 0 <= idx < max_pages:
                    indices.add(idx)
    except Exception as e:
        print(f"--- PDF Reader Warning: Invalid page range '{page_input}'. Defaulting to all pages. Reason: {e} ---")
        return range(max_pages)
    
    return sorted(list(indices))

def run(payload):
    """
    Extracts text content from a PDF file, page by page.
    Automatically uses OCR if text extraction fails (e.g., scanned images).
    """
    filename = payload.get("filename")
    password = payload.get("password")
    # Get page range (e.g., "1, 3-5") or list [1, 3, 5]
    page_range_input = payload.get("pages") 
    ocr_mode = payload.get("ocr_mode", "auto").lower() # "auto", "force", "off"

    if not filename:
        return "Error: Missing 'filename' for the PDF file."
    if not os.path.isfile(filename):
         return f"Error: PDF file '{filename}' does not exist or is not a file."

    page_contents: List[str] = []
    doc = None
    
    try:
        doc = fitz.open(filename)
        
        # 1. Handle Encryption
        if doc.is_encrypted:
            if not password:
                return f"Error: File '{filename}' is encrypted. A 'password' is required in the payload."
            if not doc.authenticate(password):
                return f"Error: Invalid password for '{filename}'."
        
        # 2. Parse Page Range
        page_indices = parse_page_range(page_range_input, doc.page_count)
        if not page_indices:
             return f"Warning: Page range '{page_range_input}' is invalid or empty for document with {doc.page_count} pages."

        # 3. Extract Text
        for page_num in page_indices:
            page = doc.load_page(page_num)
            page_text = ""
            
            # --- Text Extraction ---
            if ocr_mode != "force":
                page_text = page.get_text("text").strip()
            
            # --- OCR Fallback/Forced ---
            # If text is empty (scanned doc) and mode is 'auto', OR if mode is 'force'
            if (ocr_mode == "auto" and not page_text) or ocr_mode == "force":
                print(f"--- PDF Reader Info: Using OCR for page {page_num + 1} ---")
                try:
                    # Render page to a high-res image
                    pix = page.get_pixmap(dpi=300)
                    img_data = pix.tobytes("png")
                    pil_image = Image.open(io.BytesIO(img_data))
                    
                    # Run Tesseract OCR on the image
                    ocr_text = pytesseract.image_to_string(pil_image)
                    page_text = ocr_text.strip()
                except Exception as ocr_e:
                    print(f"--- PDF Reader Error: OCR failed for page {page_num + 1}. Reason: {ocr_e} ---")
                    # Check if Tesseract is installed
                    if "Tesseract is not installed" in str(ocr_e):
                         return "Error: 'pytesseract' failed because the Tesseract-OCR engine is not installed on the system."
                    page_text = f"[OCR Error on page {page_num + 1}]"
            
            page_contents.append(page_text)

        doc.close()

        if not page_contents:
            return f"Warning: No text could be extracted from '{filename}' (pages: {page_range_input})."
        
        # Return a list of strings (one per page)
        return page_contents

    except Exception as e:
        if doc:
            doc.close()
        print(traceback.format_exc())
        return f"Error reading PDF file '{filename}'. Reason: {e}"