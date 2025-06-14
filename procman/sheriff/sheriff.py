import requests
from typing import Dict, List, Optional
import time
import threading
import logging
from ..common.process_info import ProcessInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Sheriff:
    """Sheriff process manager that controls remote Deputies."""
    
    def __init__(self):
        self.deputies: Dict[str, str] = {}  # hostname -> url
        self.processes: Dict[str, ProcessInfo] = {}
        self._update_thread: Optional[threading.Thread] = None
        self._should_stop = False
    
    def add_deputy(self, url: str) -> bool:
        """Add a Deputy to manage."""
        try:
            if not url.startswith('http'):
                url = f'http://{url}'
            logger.info(f"Attempting to add deputy at {url}")
            response = requests.get(f"{url}/health")
            if response.status_code == 200:
                hostname = response.json()["hostname"]
                self.deputies[hostname] = url
                logger.info(f"Successfully added deputy {hostname} at {url}")
                return True
            else:
                logger.error(f"Failed to add deputy at {url}, status code: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to connect to deputy at {url}: {str(e)}")
        return False
    
    def remove_deputy(self, hostname: str) -> bool:
        """Remove a Deputy."""
        if hostname in self.deputies:
            del self.deputies[hostname]
            # Remove processes associated with this deputy
            self.processes = {
                name: proc for name, proc in self.processes.items()
                if proc.host != hostname
            }
            logger.info(f"Removed deputy {hostname}")
            return True
        logger.warning(f"Deputy {hostname} not found")
        return False
    
    def start_process(self, process_info: ProcessInfo) -> bool:
        """Start a process on a Deputy."""
        if process_info.host not in self.deputies:
            logger.error(f"No deputy found for host {process_info.host}")
            return False
            
        try:
            url = self.deputies[process_info.host]
            response = requests.post(
                f"{url}/process/start",
                json=process_info.to_dict()
            )
            if response.status_code == 200:
                self.processes[process_info.name] = process_info
                logger.info(f"Started process {process_info.name} on {process_info.host}")
                return True
            else:
                logger.error(f"Failed to start process {process_info.name}, status code: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to start process {process_info.name}: {str(e)}")
        return False
    
    def stop_process(self, name: str) -> bool:
        """Stop a process on a Deputy."""
        if name not in self.processes:
            logger.error(f"Process {name} not found")
            return False
            
        process = self.processes[name]
        if process.host not in self.deputies:
            logger.error(f"No deputy found for host {process.host}")
            return False
            
        try:
            url = self.deputies[process.host]
            response = requests.post(f"{url}/process/stop/{name}")
            if response.status_code == 200:
                logger.info(f"Stopped process {name}")
                return True
            else:
                logger.error(f"Failed to stop process {name}, status code: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to stop process {name}: {str(e)}")
        return False
    
    def restart_process(self, name: str) -> bool:
        """Restart a process on a Deputy."""
        if name not in self.processes:
            logger.error(f"Process {name} not found")
            return False
            
        process = self.processes[name]
        if process.host not in self.deputies:
            logger.error(f"No deputy found for host {process.host}")
            return False
            
        try:
            url = self.deputies[process.host]
            response = requests.post(f"{url}/process/restart/{name}")
            if response.status_code == 200:
                logger.info(f"Restarted process {name}")
                return True
            else:
                logger.error(f"Failed to restart process {name}, status code: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to restart process {name}: {str(e)}")
        return False
    
    def get_process_info(self, name: str) -> Optional[ProcessInfo]:
        """Get information about a specific process."""
        if name not in self.processes:
            return None
            
        process = self.processes[name]
        if process.host not in self.deputies:
            return None
            
        try:
            url = self.deputies[process.host]
            response = requests.get(f"{url}/process/{name}")
            if response.status_code == 200:
                data = response.json()
                return ProcessInfo.from_dict(data)
            else:
                logger.error(f"Failed to get info for process {name}, status code: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to get info for process {name}: {str(e)}")
        return None
    
    def get_all_processes(self) -> List[ProcessInfo]:
        """Get information about all processes across all Deputies."""
        processes = []
        for hostname, url in self.deputies.items():
            try:
                response = requests.get(f"{url}/processes")
                if response.status_code == 200:
                    for proc_data in response.json():
                        processes.append(ProcessInfo.from_dict(proc_data))
                else:
                    logger.error(f"Failed to get processes from {hostname}, status code: {response.status_code}")
            except requests.RequestException as e:
                logger.error(f"Failed to get processes from {hostname}: {str(e)}")
        return processes
    
    def get_deputy_status(self) -> List[Dict[str, str]]:
        """Get status of all deputies."""
        status_list = []
        for hostname, url in self.deputies.items():
            try:
                response = requests.get(f"{url}/health")
                if response.status_code == 200:
                    status = "healthy"
                else:
                    status = f"unhealthy (status: {response.status_code})"
            except requests.RequestException as e:
                status = f"unreachable ({str(e)})"
            
            status_list.append({
                "hostname": hostname,
                "url": url,
                "status": status
            })
        return status_list
    
    def load_config(self, config_file: str) -> None:
        """Load process configuration from a JSON file."""
        import json
        logger.info(f"Loading config from {config_file}")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            # Add deputies
            for deputy_url in config.get("deputies", []):
                logger.info(f"Adding deputy from config: {deputy_url}")
                self.add_deputy(deputy_url)
                
            # Add processes
            for proc_config in config.get("processes", []):
                logger.info(f"Adding process from config: {proc_config}")
                process_info = ProcessInfo.from_dict(proc_config)
                if process_info.host in self.deputies and process_info.autostart:
                    self.start_process(process_info)
                else:
                    logger.warning(f"Skipping process {process_info.name}: deputy {process_info.host} not found")
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
    
    def start_update_thread(self, interval: float = 1.0) -> None:
        """Start a thread to periodically update process information."""
        def update_loop():
            while not self._should_stop:
                for process in self.get_all_processes():
                    self.processes[process.name] = process
                time.sleep(interval)
        
        self._should_stop = False
        self._update_thread = threading.Thread(target=update_loop, daemon=True)
        self._update_thread.start()
    
    def stop_update_thread(self) -> None:
        """Stop the update thread."""
        if self._update_thread:
            self._should_stop = True
            self._update_thread.join()
            self._update_thread = None 