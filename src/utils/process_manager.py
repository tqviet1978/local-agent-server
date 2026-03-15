"""
Process Manager - Shared state for managing long-running processes
"""
import subprocess
import threading
import os
from datetime import datetime
from pathlib import Path

# Global dictionary to store running processes
_processes = {}
_lock = threading.Lock()


class ManagedProcess:
    def __init__(self, name, command, working_dir, env, log_file, pid, process):
        self.name = name
        self.command = command
        self.working_dir = working_dir
        self.env = env
        self.log_file = log_file
        self.pid = pid
        self.process = process
        self.started_at = datetime.now()
    
    def is_running(self):
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def get_status(self):
        if self.is_running():
            return "running"
        elif self.process.returncode == 0:
            return "completed"
        else:
            return "failed"
    
    def get_uptime(self):
        if not self.is_running():
            return None
        delta = datetime.now() - self.started_at
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def to_dict(self):
        return {
            "id": self.name,
            "pid": self.pid,
            "command": self.command,
            "working_dir": self.working_dir,
            "status": self.get_status(),
            "started_at": self.started_at.isoformat(),
            "uptime": self.get_uptime(),
            "log_file": self.log_file
        }


def start_process(name, command, working_dir, env=None, log_file=None):
    """Start a new managed process"""
    with _lock:
        # Check if process with same name already exists and is running
        if name in _processes and _processes[name].is_running():
            raise Exception(f"Process '{name}' is already running")
        
        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        # Prepare log file
        log_handle = None
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = open(log_path, "a")
        
        # Start process
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=working_dir,
                env=process_env,
                stdout=log_handle or subprocess.PIPE,
                stderr=log_handle or subprocess.STDOUT,
                start_new_session=True  # Detach from parent
            )
        except Exception as e:
            if log_handle:
                log_handle.close()
            raise e
        
        # Store managed process
        managed = ManagedProcess(
            name=name,
            command=command,
            working_dir=working_dir,
            env=env,
            log_file=log_file,
            pid=process.pid,
            process=process
        )
        _processes[name] = managed
        
        return managed


def stop_process(name, force=False):
    """Stop a managed process"""
    with _lock:
        if name not in _processes:
            raise Exception(f"Process '{name}' not found")
        
        managed = _processes[name]
        
        if not managed.is_running():
            # Clean up
            del _processes[name]
            return {"status": "already_stopped"}
        
        import signal
        if force:
            os.killpg(os.getpgid(managed.pid), signal.SIGKILL)
        else:
            os.killpg(os.getpgid(managed.pid), signal.SIGTERM)
        
        # Wait a bit for process to terminate
        try:
            managed.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if not force:
                os.killpg(os.getpgid(managed.pid), signal.SIGKILL)
                managed.process.wait(timeout=5)
        
        del _processes[name]
        return {"status": "stopped", "pid": managed.pid}


def get_process_status(name=None):
    """Get status of process(es)"""
    with _lock:
        if name:
            if name not in _processes:
                return None
            return _processes[name].to_dict()
        else:
            # Return all processes
            return [p.to_dict() for p in _processes.values()]


def get_process_logs(name, lines=100):
    """Get logs from a process"""
    with _lock:
        if name not in _processes:
            raise Exception(f"Process '{name}' not found")
        
        managed = _processes[name]
        
        if not managed.log_file:
            return {"error": "No log file configured for this process"}
        
        log_path = Path(managed.log_file)
        if not log_path.exists():
            return {"logs": "", "lines": 0}
        
        with open(log_path, "r") as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:] if lines else all_lines
            return {
                "logs": "".join(tail_lines),
                "lines": len(tail_lines),
                "total_lines": len(all_lines)
            }
