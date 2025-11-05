# src/aura_core/apprentices/process_manager.py
import sys
import os
import signal
import psutil # New dependency
import traceback
from typing import List

def _get_processes(pid: int = None, name: str = None) -> List[psutil.Process]:
    """Finds processes by PID or name."""
    if pid:
        try:
            return [psutil.Process(int(pid))]
        except psutil.NoSuchProcess:
            return []
    
    if name:
        found_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            if name.lower() in proc.info['name'].lower():
                found_processes.append(proc)
        return found_processes
        
    return []

def run(payload):
    """Pauses, resumes, terminates, kills, or gets info on a process."""
    if sys.platform == "win32":
        return "Error: Process management is not supported on Windows."
        
    try:
        pid = payload.get("pid")
        name = payload.get("name")
        action = payload.get("action")

        if not action:
            return "Error: Missing 'action' (must be 'pause', 'resume', 'terminate', 'kill', 'info')."
        if not pid and not name:
            return "Error: Missing 'pid' or 'name' of the target process."

        # Prioritize PID if both are given
        if pid:
            processes = _get_processes(pid=pid)
            target_desc = f"PID {pid}"
        else:
            processes = _get_processes(name=name)
            target_desc = f"name '{name}'"
        
        if not processes:
            return f"Error: No process found with {target_desc}."

        results = []
        
        for proc in processes:
            try:
                if action == "pause":
                    proc.suspend() # Uses SIGSTOP
                    results.append(f"Paused {proc.pid} ({proc.name()})")
                elif action == "resume":
                    proc.resume() # Uses SIGCONT
                    results.append(f"Resumed {proc.pid} ({proc.name()})")
                elif action == "terminate":
                    proc.terminate() # Uses SIGTERM (graceful)
                    results.append(f"Sent terminate signal to {proc.pid} ({proc.name()})")
                elif action == "kill":
                    proc.kill() # Uses SIGKILL (forceful)
                    results.append(f"Sent kill signal to {proc.pid} ({proc.name()})")
                elif action == "info":
                    # Get detailed info
                    with proc.oneshot(): # Efficiently get all info at once
                        info = {
                            "pid": proc.pid,
                            "name": proc.name(),
                            "status": proc.status(),
                            "cpu_percent": proc.cpu_percent(interval=None), # Use last interval
                            "memory_percent": f"{proc.memory_percent():.2f}%",
                            "username": proc.username()
                        }
                    results.append(info)
                else:
                    return "Error: Invalid action. Must be 'pause', 'resume', 'terminate', 'kill', or 'info'."
            
            except psutil.NoSuchProcess:
                results.append(f"Process {proc.pid} no longer exists.")
            except psutil.AccessDenied:
                results.append(f"Access denied to manage {proc.pid} ({proc.name()}).")

        # If action was 'info', return the list of dicts
        if action == "info":
            return results
            
        # Otherwise, return a success message
        return f"Success: Performed '{action}' on {len(results)} process(es). Details: {', '.join(results)}"

    except Exception as e:
        traceback.print_exc()
        return f"Error managing process. Reason: {e}"