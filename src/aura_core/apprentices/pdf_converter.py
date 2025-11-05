# src/aura_core/apprentices/pdf_converter.py
import os
import sys
import shutil
import subprocess
import traceback
from typing import Optional

# Conditionally import MS Office library only on Windows
try:
    if sys.platform == "win32":
        import win32com.client
        from pywintypes import com_error
except ImportError:
    print("--- PDF Converter Info: 'pywin32' not installed. MS Office conversion will be unavailable. ---")
    win32com = None
    com_error = None

def _find_soffice_path() -> Optional[str]:
    """Finds the path to the LibreOffice executable."""
    if sys.platform == "win32":
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        for path in paths:
            if os.path.exists(path):
                return path
    else:
        # On Linux/macOS, 'soffice' is usually in the system PATH
        path = shutil.which("soffice")
        if path:
            return path
            
    return None # Not found

def _try_msoffice_conversion(input_path: str, output_path: str) -> bool:
    """Attempts to convert using MS Office COM automation. Returns True on success."""
    if not win32com:
        print("--- PDF Converter Info: MS Office conversion skipped (pywin32 not loaded). ---")
        return False

    app = None
    doc = None
    app_name = None
    wdFormatPDF = 17 # Word
    ppFormatPDF = 32 # PowerPoint
    
    try:
        if input_path.lower().endswith(('.doc', '.docx')):
            app_name = "Word.Application"
            file_format = wdFormatPDF
        elif input_path.lower().endswith(('.ppt', '.pptx')):
            app_name = "PowerPoint.Application"
            file_format = ppFormatPDF
        else:
            return False # Unsupported file type for this method

        print(f"--- PDF Converter: Attempting conversion with {app_name}... ---")
        app = win32com.client.Dispatch(app_name)
        app.Visible = False
        
        if app_name == "Word.Application":
            doc = app.Documents.Open(input_path)
            doc.SaveAs(output_path, FileFormat=file_format)
        elif app_name == "PowerPoint.Application":
            doc = app.Presentations.Open(input_path, WithWindow=False)
            doc.SaveAs(output_path, FileFormat=file_format)

        print(f"--- PDF Converter (MS Office): Success. ---")
        return True

    except com_error as e:
        print(f"--- PDF Converter (MS Office) Warning: COM error. Is MS Office installed? {e} ---")
        return False
    except Exception as e:
        print(f"--- PDF Converter (MS Office) Warning: Failed. {e} ---")
        return False
    finally:
        # Crucial: Close the document and quit the app
        try:
            if doc: doc.Close(False) # False = Do not save changes
        except: pass
        try:
            if app: app.Quit()
        except: pass

def _try_libreoffice_conversion(input_path: str, output_dir: str) -> bool:
    """Attempts to convert using LibreOffice. Returns True on success."""
    soffice_path = _find_soffice_path()
    if not soffice_path:
        print("--- PDF Converter Info: LibreOffice conversion skipped (soffice not found). ---")
        return False

    print(f"--- PDF Converter: Attempting conversion with LibreOffice... ---")
    try:
        command = [
            soffice_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            input_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=True, encoding='utf-8')
        
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_pdf = os.path.join(output_dir, f"{base_name}.pdf")
        
        if os.path.exists(output_pdf):
            print(f"--- PDF Converter (LibreOffice): Success. ---")
            return True
        else:
            print(f"--- PDF Converter (LibreOffice) Error Log: {result.stdout} {result.stderr} ---")
            return False

    except subprocess.CalledProcessError as e:
        print(f"--- PDF Converter (LibreOffice) Error Log: {e.stderr} ---")
        return False
    except Exception as e:
        print(f"--- PDF Converter (LibreOffice) Warning: Failed. {e} ---")
        return False

def run(payload):
    """
    Converts a .docx or .pptx file to .pdf using the best available method.
    Tries MS Office first (on Windows), then falls back to LibreOffice.
    """
    input_file = payload.get("input_file")
    
    if not input_file:
        return "Error: Missing 'input_file' in payload."
    if not os.path.exists(input_file):
        return f"Error: Input file not found at '{input_file}'."
        
    input_file_abs = os.path.abspath(input_file)
    output_dir = os.path.dirname(input_file_abs)
    base_name = os.path.splitext(os.path.basename(input_file_abs))[0]
    output_pdf = os.path.join(output_dir, f"{base_name}.pdf")

    try:
        # --- Strategy: Try MS Office first (if on Windows), then LibreOffice ---
        
        success = False
        
        if sys.platform == "win32":
            success = _try_msoffice_conversion(input_file_abs, output_pdf)
        
        if not success:
            # If not Windows, or if MS Office failed, try LibreOffice
            success = _try_libreoffice_conversion(input_file_abs, output_dir)
            
        if success:
            return output_pdf # Return the new PDF file path
        else:
            return "Error: All PDF conversion methods failed. Please ensure MS Office or LibreOffice is installed."
            
    except Exception as e:
        traceback.print_exc()
        return f"Error converting file '{input_file}' to PDF. Reason: {e}"