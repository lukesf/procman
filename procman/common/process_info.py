from dataclasses import dataclass
from typing import Optional, Dict, Any
import time


@dataclass
class ProcessInfo:
    """Class to store process information and statistics."""
    name: str
    command: str
    working_dir: str
    autostart: bool = False
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    status: str = "stopped"
    start_time: Optional[float] = None
    host: str = "localhost"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ProcessInfo to dictionary."""
        return {
            "name": self.name,
            "command": self.command,
            "working_dir": self.working_dir,
            "autostart": self.autostart,
            "pid": self.pid,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "status": self.status,
            "start_time": self.start_time,
            "host": self.host,
            "uptime": time.time() - (self.start_time or time.time()) if self.start_time else 0
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessInfo':
        """Create ProcessInfo from dictionary."""
        return cls(
            name=data["name"],
            command=data["command"],
            working_dir=data["working_dir"],
            autostart=data.get("autostart", False),
            pid=data.get("pid"),
            cpu_percent=data.get("cpu_percent", 0.0),
            memory_percent=data.get("memory_percent", 0.0),
            status=data.get("status", "stopped"),
            start_time=data.get("start_time"),
            host=data.get("host", "localhost")
        ) 