# src/aura_core/apprentices/file_reader.py

def run(payload):
    """Reads the content of a specified file."""
    filename = payload.get("filename")
    if not filename:
        return "Error: Missing 'filename' in payload."

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File not found at {filename}"
    except Exception as e:
        return f"Error: Failed to read file {filename}. Reason: {e}"