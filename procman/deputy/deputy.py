from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn
import socket
import psutil
import threading
import queue
import select
import subprocess
import time
import logging
from ..common.process_manager import ProcessManager
from ..common.process_info import ProcessInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
deputy: 'Deputy' = None


class Deputy(ProcessManager):
    """Deputy process manager that runs on remote machines."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        super().__init__()
        self.host = host
        self.port = port
        self.hostname = socket.gethostname()
        self._output_threads: Dict[str, threading.Thread] = {}
        self._output_queues: Dict[str, queue.Queue] = {}
    
    def start(self):
        """Start the Deputy server."""
        global deputy
        deputy = self
        # Initialize process handles for any existing processes
        for process in self.processes.values():
            if process.status == "running" and process.pid:
                try:
                    self._process_handles[process.name] = psutil.Process(process.pid)
                except psutil.NoSuchProcess:
                    process.status = "stopped"
                    process.pid = None
        
        # Start the FastAPI server
        uvicorn.run(app, host=self.host, port=self.port)
    
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
                start_new_session=True,
                bufsize=1,
                universal_newlines=True
            )
            
            process_info.pid = process.pid
            process_info.status = "running"
            process_info.start_time = time.time()
            
            self._process_handles[process_info.name] = process
            self.processes[process_info.name] = process_info
            
            # Start output capture thread
            self._output_queues[process_info.name] = queue.Queue()
            thread = threading.Thread(
                target=self._capture_output,
                args=(process_info.name, process),
                daemon=True
            )
            thread.start()
            self._output_threads[process_info.name] = thread
            
            return True
            
        except Exception as e:
            process_info.status = f"error: {str(e)}"
            return False
    
    def stop_process(self, name: str) -> bool:
        """Stop a process."""
        success = super().stop_process(name)
        if success:
            # Clean up output capture
            if name in self._output_threads:
                self._output_threads[name].join(timeout=1)
                del self._output_threads[name]
            if name in self._output_queues:
                del self._output_queues[name]
        return success
    
    def _capture_output(self, name: str, process: subprocess.Popen) -> None:
        """Capture process output in a separate thread."""
        while True:
            # Use select to avoid blocking
            reads = [process.stdout, process.stderr]
            ready, _, _ = select.select(reads, [], [], 0.1)
            
            for fd in ready:
                line = fd.readline()
                if line:
                    if fd == process.stdout:
                        self.processes[name].add_output(stdout=line.strip())
                    else:
                        self.processes[name].add_output(stderr=line.strip())
            
            # Check if process has ended
            if process.poll() is not None:
                # Read any remaining output
                stdout, stderr = process.communicate()
                if stdout:
                    self.processes[name].add_output(stdout=stdout.strip())
                if stderr:
                    self.processes[name].add_output(stderr=stderr.strip())
                break
    
    def get_system_stats(self) -> Dict[str, float]:
        """Get system statistics."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    stats = deputy.get_system_stats()
    return {
        "status": "healthy",
        "hostname": deputy.hostname,
        **stats
    }


@app.post("/process/start")
async def start_process(process_info: Dict[str, Any]):
    """Start a process."""
    proc_info = ProcessInfo.from_dict(process_info)
    success = deputy.start_process(proc_info)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to start process {proc_info.name}")
    return {"status": "success"}


@app.post("/process/stop/{name}")
async def stop_process(name: str):
    """Stop a process."""
    success = deputy.stop_process(name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to stop process {name}")
    return {"status": "success"}


@app.post("/process/restart/{name}")
async def restart_process(name: str):
    """Restart a process."""
    success = deputy.restart_process(name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to restart process {name}")
    return {"status": "success"}


@app.get("/process/{name}")
async def get_process_info(name: str):
    """Get information about a specific process."""
    deputy.update_process_stats(name)
    process_info = deputy.get_process_info(name)
    if not process_info:
        raise HTTPException(status_code=404, detail=f"Process {name} not found")
    return process_info.to_dict()


@app.get("/processes")
async def get_all_processes():
    """Get information about all processes."""
    for process in deputy.get_all_processes():
        deputy.update_process_stats(process.name)
    return [p.to_dict() for p in deputy.get_all_processes()]


def main(host: str = "0.0.0.0", port: int = 8000):
    """Start the Deputy process manager."""
    global deputy
    deputy = Deputy(host=host, port=port)
    deputy.start()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deputy Process Manager")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    main(host=args.host, port=args.port) 