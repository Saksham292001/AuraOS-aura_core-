# src/aura_core/apprentices/file_writer.py
import json
import os
import traceback
from typing import Union, Dict, List

def run(payload):
    """
    Writes content to a file.
    Automatically handles directory creation.
    Intelligently saves dict/list as JSON.
    """
    filename = payload.get("filename")
    content = payload.get("content")
    action = payload.get("action", "write").lower() # Default to "write", allow "append"
    
    if not filename or content is None:
        return "Error: Missing 'filename' or 'content' in payload."

    if action not in ["write", "append"]:
        return f"Error: Invalid action '{action}'. Use 'write' or 'append'."

    try:
        # --- Automatic Directory Creation ---
        file_dir = os.path.dirname(filename)
        if file_dir and not os.path.exists(file_dir):
            try:
                os.makedirs(file_dir, exist_ok=True)
                print(f"--- File Writer: Created directory '{file_dir}' ---")
            except Exception as e:
                return f"Error: Could not create directory '{file_dir}'. Reason: {e}"

        # Determine file mode
        mode = 'w' if action == "write" else 'a'
        
        # --- Automatic JSON Writing ---
        if isinstance(content, (dict, list)):
            # If content is dict/list, write as pretty-printed JSON
            with open(filename, mode, encoding='utf-8') as f:
                json.dump(content, f, indent=4)
            return f"Success: Wrote JSON content to {filename}"
        
        else:
            # Otherwise, write as plain text
            with open(filename, mode, encoding='utf-8') as f:
                f.write(str(content))
            return f"Success: Wrote {len(str(content))} characters to {filename} (mode: {action})."

    except Exception as e:
        traceback.print_exc()
        return f"Error: Failed to write to file {filename}. Reason: {e}"