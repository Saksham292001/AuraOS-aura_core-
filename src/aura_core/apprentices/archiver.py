# src/aura_core/apprentices/archiver.py
import os
import zipfile
import shutil
import traceback
from typing import List

def create_zip_from_folder(source_folder, zip_filename):
    """Zips an entire folder."""
    if not os.path.isdir(source_folder):
        return f"Error: Source folder '{source_folder}' does not exist."
    
    # shutil.make_archive wants the base name of the output, not the full .zip filename
    base_name = os.path.splitext(zip_filename)[0]
    # It also needs the root directory (what to zip)
    root_dir = os.path.dirname(source_folder) or '.'
    # And the name of the folder within that root dir
    folder_name = os.path.basename(source_folder)
    
    try:
        shutil.make_archive(base_name, 'zip', root_dir, folder_name)
        return f"Success: Created archive '{zip_filename}' from folder '{source_folder}'."
    except Exception as e:
        return f"Error creating archive from folder: {e}"

def create_zip_from_files(file_list: List[str], zip_filename: str):
    """Zips a specific list of files."""
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in file_list:
                if os.path.isfile(file_path):
                    # arcname preserves the file's base name inside the zip
                    zf.write(file_path, arcname=os.path.basename(file_path))
                else:
                    print(f"--- Archiver Warning: File not found '{file_path}'. Skipping. ---")
        return f"Success: Created archive '{zip_filename}' with {len(file_list)} files."
    except Exception as e:
        return f"Error creating archive from files: {e}"

def extract_archive(zip_filename, destination_folder, password=None):
    """Extracts a full archive."""
    if not os.path.isfile(zip_filename):
        return f"Error: Zip file '{zip_filename}' does not exist."
    try:
        with zipfile.ZipFile(zip_filename, 'r') as zf:
            pwd = bytes(password, 'utf-8') if password else None
            zf.extractall(destination_folder, pwd=pwd)
        return f"Success: Extracted '{zip_filename}' to '{destination_folder}'."
    except RuntimeError as e:
        if "password" in str(e).lower():
            return f"Error: Extraction failed. Is the password '{password}' correct?"
        return f"Error: Failed to extract. Reason: {e}"
    except Exception as e:
        return f"Error extracting archive: {e}"

def extract_specific_files(zip_filename, destination_folder, file_list: List[str], password=None):
    """Extracts only specific files from an archive."""
    if not os.path.isfile(zip_filename):
        return f"Error: Zip file '{zip_filename}' does not exist."
    try:
        with zipfile.ZipFile(zip_filename, 'r') as zf:
            pwd = bytes(password, 'utf-8') if password else None
            for file_path in file_list:
                try:
                    # Extract one file. It preserves path structure.
                    zf.extract(file_path, destination_folder, pwd=pwd)
                except KeyError:
                    print(f"--- Archiver Warning: File '{file_path}' not found in zip. Skipping. ---")
                except Exception as e_file:
                     print(f"--- Archiver Warning: Could not extract '{file_path}'. Reason: {e_file} ---")
        return f"Success: Extracted {len(file_list)} requested files from '{zip_filename}'."
    except RuntimeError as e:
        if "password" in str(e).lower():
            return f"Error: Extraction failed. Is the password '{password}' correct?"
        return f"Error: Failed to extract files. Reason: {e}"
    except Exception as e:
        return f"Error extracting files: {e}"

def list_archive_contents(zip_filename):
    """Lists the contents of an archive."""
    if not os.path.isfile(zip_filename):
        return f"Error: Zip file '{zip_filename}' does not exist."
    try:
        with zipfile.ZipFile(zip_filename, 'r') as zf:
            return zf.namelist()
    except Exception as e:
        return f"Error listing contents of '{zip_filename}'. Reason: {e}"

def run(payload):
    """Creates or extracts ZIP archives."""
    action = payload.get("action")
    zip_filename = payload.get("zip_filename")
    
    if not action:
        return "Error: Missing 'action' in payload. Use 'create', 'create_files', 'extract', 'extract_files', or 'list'."
    if not zip_filename:
         return f"Error: Missing 'zip_filename' for '{action}' action."
         
    # Ensure .zip extension
    if not zip_filename.lower().endswith('.zip'):
        zip_filename += '.zip'
        
    try:
        if action == "create":
            source_folder = payload.get("source_folder")
            if not source_folder:
                return "Error: Missing 'source_folder' for 'create' action."
            return create_zip_from_folder(source_folder, zip_filename)

        elif action == "create_files":
            files = payload.get("files")
            if not files or not isinstance(files, list):
                return "Error: Missing 'files' list for 'create_files' action."
            return create_zip_from_files(files, zip_filename)

        elif action == "extract":
            destination_folder = payload.get("destination_folder")
            password = payload.get("password")
            if not destination_folder:
                return "Error: Missing 'destination_folder' for 'extract' action."
            os.makedirs(destination_folder, exist_ok=True)
            return extract_archive(zip_filename, destination_folder, password)
            
        elif action == "extract_files":
            destination_folder = payload.get("destination_folder")
            files = payload.get("files")
            password = payload.get("password")
            if not destination_folder:
                return "Error: Missing 'destination_folder' for 'extract_files' action."
            if not files or not isinstance(files, list):
                return "Error: Missing 'files' list for 'extract_files' action."
            os.makedirs(destination_folder, exist_ok=True)
            return extract_specific_files(zip_filename, destination_folder, files, password)

        elif action == "list":
            return list_archive_contents(zip_filename)

        else:
            return f"Error: Unknown action '{action}'. Use 'create', 'create_files', 'extract', 'extract_files', or 'list'."

    except Exception as e:
        traceback.print_exc()
        return f"Error performing '{action}' on '{zip_filename}'. Reason: {e}"