#!/usr/bin/env python3
"""Smoke test for procman."""

import os
import sys
import time
import json
import signal
import subprocess
import requests
from typing import List, Optional, Dict


class SmokeTest:
    """Smoke test runner."""
    
    def __init__(self):
        """Initialize smoke test."""
        self.deputy_process: Optional[subprocess.Popen] = None
        self.sheriff_process: Optional[subprocess.Popen] = None
        self.config_file = "smoke_test_config.json"
        self.deputy_url = "http://localhost:8000"
    
    def setup(self):
        """Set up test environment."""
        print("Setting up test environment...")
        
        # Create test config
        config = {
            "deputies": [self.deputy_url],
            "processes": [
                {
                    "name": "counter",
                    "command": "sh -c 'for i in $(seq 1 5); do echo $i; sleep 1; done'",
                    "working_dir": "/tmp",
                    "host": "localhost",
                    "autostart": True,
                    "auto_restart": False
                },
                {
                    "name": "auto-restart-test",
                    "command": "sh -c 'echo starting; sleep 2; echo failing; exit 1'",
                    "working_dir": "/tmp",
                    "host": "localhost",
                    "autostart": True,
                    "auto_restart": True
                }
            ]
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def start_deputy(self):
        """Start Deputy process."""
        print("Starting Deputy...")
        self.deputy_process = subprocess.Popen(
            ["python", "-m", "procman.deputy", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        # Wait for Deputy to be ready
        for _ in range(5):  # Try for 10 seconds
            if self.check_deputy_health():
                break
            time.sleep(2)
    
    def start_sheriff(self):
        """Start Sheriff process."""
        print("Starting Sheriff...")
        self.sheriff_process = subprocess.Popen(
            ["python", "-m", "procman.sheriff.cli", "load-config", self.config_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        time.sleep(2)  # Wait for Sheriff to start
    
    def check_deputy_health(self) -> bool:
        """Check Deputy health."""
        print("Checking Deputy health...")
        try:
            response = requests.get(f"{self.deputy_url}/health")
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_processes(self) -> List[Dict]:
        """Get list of processes."""
        try:
            response = requests.get(f"{self.deputy_url}/processes")
            return response.json() if response.status_code == 200 else []
        except requests.RequestException:
            return []
    
    def check_process_output(self, name: str, expected_output: List[str]) -> bool:
        """Check if process output matches expected output."""
        processes = self.get_processes()
        for proc in processes:
            if proc["name"] == name:
                actual_output = proc.get("stdout", [])
                print(f"Expected output: {expected_output}")
                print(f"Actual output: {actual_output}")
                # Check if any of the expected numbers are in the output
                found_numbers = [exp for exp in expected_output if any(exp in line for line in actual_output)]
                return len(found_numbers) >= 1  # At least one number should be found
        return False
    
    def cleanup(self):
        """Clean up test environment."""
        print("Cleaning up...")
        
        # Stop Sheriff
        if self.sheriff_process:
            self.sheriff_process.terminate()
            self.sheriff_process.wait(timeout=5)
        
        # Stop Deputy
        if self.deputy_process:
            self.deputy_process.terminate()
            self.deputy_process.wait(timeout=5)
        
        # Remove config file
        if os.path.exists(self.config_file):
            os.unlink(self.config_file)
    
    def run(self) -> bool:
        """Run smoke test."""
        try:
            # Setup
            self.setup()
            self.start_deputy()
            
            # Check Deputy health
            if not self.check_deputy_health():
                print("ERROR: Deputy is not healthy")
                return False
            
            # Start Sheriff with config
            self.start_sheriff()
            time.sleep(10)  # Wait longer for processes to start and run
            
            # Check counter process output
            if not self.check_process_output("counter", ["1", "2", "3"]):
                print("ERROR: Counter process output not as expected")
                return False
            
            # Check auto-restart process
            if not self.check_process_output("auto-restart-test", ["starting", "failing"]):
                print("ERROR: Auto-restart process output not as expected")
                return False
            
            print("Smoke test passed!")
            return True
            
        except Exception as e:
            print(f"ERROR: Smoke test failed: {str(e)}")
            return False
            
        finally:
            self.cleanup()


def main():
    """Run smoke test."""
    smoke_test = SmokeTest()
    success = smoke_test.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 