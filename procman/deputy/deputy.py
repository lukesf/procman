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
import tempfile

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
                    # Store the psutil Process object
                    proc = psutil.Process(process.pid)
                    if proc.is_running():
                        self._process_handles[process.name] = proc
                    else:
                        process.status = "stopped"
                        process.pid = None
                except psutil.NoSuchProcess:
                    process.status = "stopped"
                    process.pid = None
        
        # Start the FastAPI server
        uvicorn.run(app, host=self.host, port=self.port)
    
    def start_process(self, process_info: ProcessInfo) -> bool:
        """Start a process."""
        if process_info.name in self._process_handles:
            try:
                proc = self._process_handles[process_info.name]
                if isinstance(proc, psutil.Process) and proc.is_running():
                    return False
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        try:
            # Handle shell commands properly
            if ' ' in process_info.command:
                args = process_info.command
                shell = True
                logger.info(f"Starting shell process {process_info.name} with command: {args}")
            else:
                args = process_info.command.split()
                shell = False
                logger.info(f"Starting process {process_info.name} with args: {args}")
            
            # Clear any existing output
            process_info.stdout_buffer.clear()
            process_info.stderr_buffer.clear()
            process_info.last_stdout_pos = 0
            process_info.last_stderr_pos = 0
            
            # Create temporary files for output
            stdout_file = tempfile.NamedTemporaryFile(mode='w+', prefix=f"{process_info.name}-stdout-")
            stderr_file = tempfile.NamedTemporaryFile(mode='w+', prefix=f"{process_info.name}-stderr-")
            
            process = subprocess.Popen(
                args,
                cwd=process_info.working_dir,
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True,
                shell=shell,
                executable='/bin/bash' if shell else None
            )
            
            # Verify process started successfully
            if process.poll() is not None:
                logger.error(f"Process {process_info.name} failed to start")
                process_info.status = "error: process exited immediately"
                stdout_file.close()
                stderr_file.close()
                return False
            
            process_info.pid = process.pid
            process_info.status = "running"
            process_info.start_time = time.time()
            
            self._process_handles[process_info.name] = process
            self.processes[process_info.name] = process_info
            
            # Start output capture thread
            thread = threading.Thread(
                target=self._capture_output,
                args=(process_info.name, process, stdout_file, stderr_file),
                daemon=True
            )
            thread.start()
            self._output_threads[process_info.name] = thread
            
            logger.info(f"Successfully started process {process_info.name} with PID {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start process {process_info.name}: {str(e)}")
            process_info.status = f"error: {str(e)}"
            # If auto-restart is enabled, try again after a short delay
            if process_info.auto_restart:
                logger.info(f"Auto-restart enabled, retrying process {process_info.name} in 5 seconds")
                threading.Timer(5.0, self.start_process, args=[process_info]).start()
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
    
    def _capture_output(self, name: str, process: subprocess.Popen, stdout_file: tempfile.NamedTemporaryFile, stderr_file: tempfile.NamedTemporaryFile) -> None:
        """Capture process output from temporary files."""
        logger.info(f"Starting output capture for process {name}")
        
        try:
            while True:
                # Check if process has ended
                if process.poll() is not None:
                    logger.info(f"Process {name} has ended, reading final output")
                    
                    # Read any remaining output
                    stdout_file.flush()
                    stderr_file.flush()
                    
                    stdout_file.seek(0)
                    stderr_file.seek(0)
                    
                    stdout = stdout_file.read()
                    stderr = stderr_file.read()
                    
                    if stdout:
                        logger.info(f"Final stdout from {name}: {stdout.strip()}")
                        self.processes[name].add_output(stdout=stdout.strip())
                    if stderr:
                        logger.info(f"Final stderr from {name}: {stderr.strip()}")
                        self.processes[name].add_output(stderr=stderr.strip())
                    
                    break
                
                # Read current output
                stdout_file.flush()
                stderr_file.flush()
                
                stdout_file.seek(0)
                stderr_file.seek(0)
                
                stdout = stdout_file.read()
                stderr = stderr_file.read()
                
                if stdout:
                    logger.info(f"Stdout from {name}: {stdout.strip()}")
                    self.processes[name].add_output(stdout=stdout.strip())
                if stderr:
                    logger.info(f"Stderr from {name}: {stderr.strip()}")
                    self.processes[name].add_output(stderr=stderr.strip())
                
                # Small sleep to prevent busy waiting
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in output capture thread for process {name}: {str(e)}")
        finally:
            # Clean up temporary files
            stdout_file.close()
            stderr_file.close()
            logger.info(f"Output capture thread for process {name} has ended")
    
    def get_system_stats(self) -> Dict[str, float]:
        """Get system statistics."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }

    def delete_process(self, name: str) -> bool:
        """Delete a process."""
        if name not in self._process_handles:
            logger.error(f"Process {name} not found")
            return False
            
        # Stop the process if it's running
        if self._process_handles[name].poll() is None:
            self.stop_process(name)
            
        # Remove from tracking
        del self._process_handles[name]
        del self._process_info[name]
        logger.info(f"Deleted process {name}")
        return True
        
    def update_process(self, name: str, process_info: ProcessInfo) -> bool:
        """Update a process configuration."""
        if name not in self._process_info:
            logger.error(f"Process {name} not found")
            return False
            
        # Store current state
        was_running = self._process_handles[name].poll() is None if name in self._process_handles else False
        
        # Update process info
        self._process_info[name] = process_info
        
        # Restart if it was running
        if was_running:
            return self.restart_process(name)
        return True


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
    if not proc_info.autostart:
        # Just add the process without starting it
        deputy.processes[proc_info.name] = proc_info
        return {"status": "success"}
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


@app.post("/process/delete/{name}")
async def delete_process(name: str):
    """Delete a process."""
    success = deputy.delete_process(name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to delete process {name}")
    return {"status": "success"}


@app.post("/process/update/{name}")
async def update_process(name: str, process_info: Dict[str, Any]):
    """Update a process configuration."""
    proc_info = ProcessInfo.from_dict(process_info)
    success = deputy.update_process(name, proc_info)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to update process {name}")
    return {"status": "success"}


@app.post("/process/add")
async def add_process(process_info: Dict[str, Any]):
    """Add a process without starting it."""
    proc_info = ProcessInfo.from_dict(process_info)
    deputy.processes[proc_info.name] = proc_info
    return {"status": "success"}


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