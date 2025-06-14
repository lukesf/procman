from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Deque
from collections import deque
import time


@dataclass
class ProcessInfo:
    """Class to store process information and statistics."""
    name: str
    command: str
    working_dir: str
    autostart: bool = False
    auto_restart: bool = False
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    status: str = "stopped"
    start_time: Optional[float] = None
    host: str = "localhost"
    stdout_buffer: Deque[str] = field(default_factory=lambda: deque(maxlen=1000))
    stderr_buffer: Deque[str] = field(default_factory=lambda: deque(maxlen=1000))
    last_stdout_pos: int = field(default=0)
    last_stderr_pos: int = field(default=0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ProcessInfo to dictionary."""
        return {
            "name": self.name,
            "command": self.command,
            "working_dir": self.working_dir,
            "autostart": self.autostart,
            "auto_restart": self.auto_restart,
            "pid": self.pid,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "status": self.status,
            "start_time": self.start_time,
            "host": self.host,
            "uptime": time.time() - (self.start_time or time.time()) if self.start_time else 0,
            "stdout": list(self.stdout_buffer),
            "stderr": list(self.stderr_buffer),
            "last_stdout_pos": self.last_stdout_pos,
            "last_stderr_pos": self.last_stderr_pos
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessInfo':
        """Create ProcessInfo from dictionary."""
        proc = cls(
            name=data["name"],
            command=data["command"],
            working_dir=data["working_dir"],
            autostart=data.get("autostart", False),
            auto_restart=data.get("auto_restart", False),
            pid=data.get("pid"),
            cpu_percent=data.get("cpu_percent", 0.0),
            memory_percent=data.get("memory_percent", 0.0),
            status=data.get("status", "stopped"),
            start_time=data.get("start_time"),
            host=data.get("host", "localhost")
        )
        
        # Add output buffers if present
        if "stdout" in data:
            proc.stdout_buffer.clear()
            proc.stdout_buffer.extend(data["stdout"])
        if "stderr" in data:
            proc.stderr_buffer.clear()
            proc.stderr_buffer.extend(data["stderr"])
        proc.last_stdout_pos = data.get("last_stdout_pos", 0)
        proc.last_stderr_pos = data.get("last_stderr_pos", 0)
        
        return proc
    
    def add_output(self, stdout: Optional[str] = None, stderr: Optional[str] = None) -> None:
        """Add output to the buffers."""
        if stdout:
            self.stdout_buffer.append(stdout)
            self.last_stdout_pos += 1
        if stderr:
            self.stderr_buffer.append(stderr)
            self.last_stderr_pos += 1 