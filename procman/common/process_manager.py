import os
import signal
import subprocess
import psutil
from typing import Dict, Optional, List
import time
import json
from .process_info import ProcessInfo


class ProcessManager:
    """Base class for process management functionality."""
    
    def __init__(self):
        self.processes: Dict[str, ProcessInfo] = {}
        self._process_handles: Dict[str, subprocess.Popen] = {}
    
    def start_process(self, process_info: ProcessInfo) -> bool:
        """Start a process."""
        if process_info.name in self._process_handles and self._process_handles[process_info.name].poll() is None:
            return False
            
        try:
            process = subprocess.Popen(
                process_info.command.split(),
                cwd=process_info.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            process_info.pid = process.pid
            process_info.status = "running"
            process_info.start_time = time.time()
            
            self._process_handles[process_info.name] = process
            self.processes[process_info.name] = process_info
            return True
            
        except Exception as e:
            process_info.status = f"error: {str(e)}"
            return False
    
    def stop_process(self, name: str) -> bool:
        """Stop a process."""
        if name not in self._process_handles:
            return False
            
        process = self._process_handles[name]
        if process.poll() is not None:
            return False
            
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            return False
            
        self.processes[name].status = "stopped"
        self.processes[name].pid = None
        self.processes[name].start_time = None
        return True
    
    def restart_process(self, name: str) -> bool:
        """Restart a process."""
        if name not in self.processes:
            return False
            
        self.stop_process(name)
        return self.start_process(self.processes[name])
    
    def update_process_stats(self, name: str) -> None:
        """Update process statistics."""
        if name not in self.processes or not self.processes[name].pid:
            return
            
        try:
            process = psutil.Process(self.processes[name].pid)
            self.processes[name].cpu_percent = process.cpu_percent()
            self.processes[name].memory_percent = process.memory_percent()
        except psutil.NoSuchProcess:
            self.processes[name].status = "died"
            self.processes[name].pid = None
            self.processes[name].cpu_percent = 0.0
            self.processes[name].memory_percent = 0.0
    
    def get_process_info(self, name: str) -> Optional[ProcessInfo]:
        """Get information about a specific process."""
        return self.processes.get(name)
    
    def get_all_processes(self) -> List[ProcessInfo]:
        """Get information about all processes."""
        return list(self.processes.values())
    
    def load_config(self, config_file: str) -> None:
        """Load process configuration from a JSON file."""
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        for proc_config in config.get("processes", []):
            process_info = ProcessInfo.from_dict(proc_config)
            self.processes[process_info.name] = process_info
            if process_info.autostart:
                self.start_process(process_info)
    
    def cleanup(self) -> None:
        """Stop all processes and cleanup."""
        for name in list(self._process_handles.keys()):
            self.stop_process(name) 