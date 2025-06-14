from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn
import socket
from ..common.process_manager import ProcessManager
from ..common.process_info import ProcessInfo

app = FastAPI()
deputy: 'Deputy' = None


class Deputy(ProcessManager):
    """Deputy process manager that runs on remote machines."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        super().__init__()
        self.host = host
        self.port = port
        self.hostname = socket.gethostname()
    
    def start(self):
        """Start the Deputy server."""
        global deputy
        deputy = self
        uvicorn.run(app, host=self.host, port=self.port)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "hostname": deputy.hostname}


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
    deputy_server = Deputy(host=host, port=port)
    deputy_server.start()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deputy Process Manager")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    main(host=args.host, port=args.port) 