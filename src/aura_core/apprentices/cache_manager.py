# src/aura_core/apprentices/cache_manager.py
import sys

def run(payload):
    """Generates the command to clear the Linux page cache."""
    if sys.platform != "linux":
        return "Error: Cache management is only supported on Linux."

    # This command requires root. We cannot run it directly.
    # We provide the command to the user as output.
    command_to_run = "sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'"
    
    return f"ACTION_REQUIRED: This action requires root. Please run the following command in your terminal:\n{command_to_run}"