# src/aura_core/apprentices/file_manager.py
import os
import shutil
import glob
import traceback
from datetime import datetime

def get_file_info(path):
    """Gets detailed info for a file or directory."""
    try:
        if not os.path.exists(path):
            return {"error": "Path does not exist."}
        
        stat = os.stat(path)
        info = {
            "path": os.path.abspath(path),
            "type": "directory" if os.path.isdir(path) else "file",
            "size_bytes": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat()
        }
        return info
    except Exception as e:
        return {"error": f"Could not get info for '{path}'. Reason: {e}"}

def list_directory(path, list_type="all"):
    """Lists contents of a directory."""
    if not os.path.isdir(path):
        return f"Error: Path '{path}' is not a valid directory."
    try:
        files = []
        dirs = []
        all_items = os.listdir(path)
        
        for item in all_items:
            if os.path.isdir(os.path.join(path, item)):
                dirs.append(item)
            else:
                files.append(item)
                
        if list_type == "files":
            return files
        elif list_type == "dirs":
            return dirs
        else: # "all"
            return {"directories": dirs, "files": files}
            
    except Exception as e:
        return f"Error listing directory '{path}'. Reason: {e}"

def run_batch_operation(action, pattern, destination=None):
    """Handles glob_copy, glob_move, and glob_delete."""
    try:
        files = glob.glob(pattern, recursive=True) # Find all matching files
        if not files:
            return f"Success: No files found matching pattern '{pattern}'."
        
        count = 0
        for file_path in files:
            try:
                if action == "glob_delete":
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path) # Be careful with rmtree on globs!
                        count += 1
                
                elif action == "glob_copy":
                    if not destination: return "Error: Missing 'destination' for glob_copy."
                    os.makedirs(destination, exist_ok=True)
                    shutil.copy2(file_path, destination)
                    count += 1
                
                elif action == "glob_move":
                    if not destination: return "Error: Missing 'destination' for glob_move."
                    os.makedirs(destination, exist_ok=True)
                    shutil.move(file_path, destination)
                    count += 1
            except Exception as e_file:
                print(f"--- File Manager Warning: Failed to {action} '{file_path}'. Reason: {e_file} ---")
        
        return f"Success: Performed '{action}' on {count} items matching '{pattern}'."
    
    except Exception as e:
        return f"Error performing batch '{action}' on '{pattern}'. Reason: {e}"


def run(payload):
    """Manages files and directories: copy, move, delete, list, info, mkdir, glob_..."""
    action = payload.get("action")
    
    try:
        if not action:
            return "Error: Missing 'action' in payload. Use 'copy', 'move', 'delete', 'list', 'info', 'mkdir', 'glob_copy', 'glob_move', 'glob_delete'."

        action = action.lower()

        # --- Batch Glob Actions ---
        if action.startswith("glob_"):
            pattern = payload.get("pattern")
            destination = payload.get("destination")
            if not pattern:
                return f"Error: Missing 'pattern' for '{action}'. Use wildcards like '*.txt' or 'logs/**/*.log'."
            return run_batch_operation(action, pattern, destination)

        # --- Single-Target Actions ---
        elif action in ["copy", "move"]:
            source = payload.get("source")
            destination = payload.get("destination")
            if not source or not destination:
                return f"Error: Missing 'source' or 'destination' for '{action}' action."
            if not os.path.exists(source):
                return f"Error: Source path '{source}' does not exist."

            dest_dir = os.path.dirname(destination)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            if action == "copy":
                if os.path.isdir(source):
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                    return f"Success: Copied directory '{source}' to '{destination}'."
                else:
                    shutil.copy2(source, destination)
                    return f"Success: Copied file '{source}' to '{destination}'."
            elif action == "move":
                shutil.move(source, destination)
                return f"Success: Moved '{source}' to '{destination}'."

        elif action == "delete":
            target = payload.get("target")
            if not target:
                return "Error: Missing 'target' for 'delete' action."
            if not os.path.exists(target):
                return f"Error: Target path '{target}' does not exist."
            
            if os.path.isdir(target):
                shutil.rmtree(target)
                return f"Success: Deleted directory '{target}'."
            else:
                os.remove(target)
                return f"Success: Deleted file '{target}'."

        elif action == "rename":
            source = payload.get("source")
            destination = payload.get("destination")
            if not source or not destination:
                return "Error: Missing 'source' or 'destination' for 'rename' action."
            if not os.path.exists(source):
                return f"Error: Source path '{source}' does not exist."
            shutil.move(source, destination)
            return f"Success: Renamed '{source}' to '{destination}'."

        elif action == "mkdir":
            path = payload.get("path")
            if not path:
                return "Error: Missing 'path' for 'mkdir' action."
            os.makedirs(path, exist_ok=True)
            return f"Success: Created directory '{path}'."

        elif action == "list":
            path = payload.get("path", ".") # Default to current directory
            list_type = payload.get("type", "all") # 'all', 'files', 'dirs'
            return list_directory(path, list_type)

        elif action == "info":
            path = payload.get("path")
            if not path:
                return "Error: Missing 'path' for 'info' action."
            return get_file_info(path)

        else:
            return f"Error: Unknown action '{action}'."

    except Exception as e:
        traceback.print_exc()
        return f"Error performing '{action}'. Reason: {e}"