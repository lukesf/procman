#!/usr/bin/env python3
"""Smoke test for Deputy process management."""

import pytest
import os
import sys
import time
import json
import subprocess
import requests
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DeputySmokeTest:
    """Deputy smoke test runner."""
    
    def __init__(self):
        """Initialize smoke test."""
        self.deputy_process: Optional[subprocess.Popen] = None
        self.deputy_url = "http://localhost:8000"
        
    def setup(self):
        """Set up test environment."""
        print("Setting up test environment...")
        self.start_deputy()
        
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
    
    def check_deputy_health(self) -> bool:
        """Check Deputy health."""
        print("Checking Deputy health...")
        try:
            response = requests.get(f"{self.deputy_url}/health")
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def test_process_lifecycle(self) -> bool:
        """Test complete process lifecycle."""
        print("\nTesting process lifecycle...")
        
        # 1. Add a stopped process
        process_info = {
            "name": "testcounter",
            "command": "while true; do echo 'test output'; sleep 1; done",
            "working_dir": "/tmp",
            "host": "localhost",
            "autostart": False,
            "auto_restart": False
        }
        
        print("Adding stopped process...")
        response = requests.post(
            f"{self.deputy_url}/process/add",
            json=process_info
        )
        if response.status_code != 200:
            print("ERROR: Failed to add process")
            return False
        print("Successfully added process")
        
        # 2. Verify process is added but not running
        response = requests.get(f"{self.deputy_url}/processes")
        if response.status_code != 200:
            print("ERROR: Failed to get processes")
            return False
        
        processes = response.json()
        if not any(p["name"] == "testcounter" and p["status"] == "stopped" for p in processes):
            print("ERROR: Process not found or not in stopped state")
            return False
        print("Successfully verified process is stopped")
        
        # 3. Start the process
        print("Starting process...")
        response = requests.post(f"{self.deputy_url}/process/start", json=process_info)
        if response.status_code != 200:
            print("ERROR: Failed to start process")
            return False
        print("Successfully started process")
        
        # Wait for some output
        print("Waiting for output...")
        max_attempts = 10
        for attempt in range(max_attempts):
            time.sleep(1)
            response = requests.get(f"{self.deputy_url}/processes")
            if response.status_code != 200:
                print("ERROR: Failed to get processes")
                return False
            
            processes = response.json()
            process = next((p for p in processes if p["name"] == "testcounter"), None)
            if process and process["status"] == "running" and process.get("stdout"):
                print(f"Got output after {attempt + 1} seconds")
                break
            if attempt == max_attempts - 1:
                print("ERROR: Process not running or no output")
                return False
        
        print("Successfully verified process is running with output")
        
        # 5. Stop the process
        print("Stopping process...")
        response = requests.post(f"{self.deputy_url}/process/stop/testcounter")
        if response.status_code != 200:
            print("ERROR: Failed to stop process")
            return False
        print("Successfully stopped process")
        
        # 6. Modify the process command
        print("Modifying process command...")
        process_info["command"] = "sh -c 'echo modified; sleep 2'"
        response = requests.post(
            f"{self.deputy_url}/process/update/testcounter",
            json=process_info
        )
        if response.status_code != 200:
            print("ERROR: Failed to update process")
            return False
        print("Successfully updated process")
        
        # Start the modified process
        response = requests.post(f"{self.deputy_url}/process/start", json=process_info)
        if response.status_code != 200:
            print("ERROR: Failed to start modified process")
            return False
        
        # Wait for output
        time.sleep(3)
        
        # Verify modified output
        response = requests.get(f"{self.deputy_url}/processes")
        if response.status_code != 200:
            print("ERROR: Failed to get processes")
            return False
        
        processes = response.json()
        process = next((p for p in processes if p["name"] == "testcounter"), None)
        if not process or "modified" not in str(process.get("stdout", [])):
            print("ERROR: Modified process output not found")
            return False
        print("Successfully verified modified process output")
        
        # 7. Delete the process
        print("Deleting process...")
        response = requests.post(f"{self.deputy_url}/process/delete/testcounter")
        if response.status_code != 200:
            print("ERROR: Failed to delete process")
            return False
        print("Successfully deleted process")
        
        # Verify process is deleted
        response = requests.get(f"{self.deputy_url}/processes")
        if response.status_code != 200:
            print("ERROR: Failed to get processes")
            return False
        
        processes = response.json()
        if any(p["name"] == "testcounter" for p in processes):
            print("ERROR: Process still exists after deletion")
            return False
        print("Successfully verified process deletion")
        
        return True
    
    def cleanup(self):
        """Clean up test environment."""
        print("\nCleaning up...")
        
        # Stop Deputy
        if self.deputy_process:
            self.deputy_process.terminate()
            self.deputy_process.wait(timeout=5)
    
    @pytest.mark.smoke
    @pytest.mark.deputy
    def run(self) -> bool:
        """Run smoke test."""
        try:
            # Setup
            self.setup()
            
            # Check Deputy health
            if not self.check_deputy_health():
                print("ERROR: Deputy is not healthy")
                return False
            
            # Run process lifecycle test
            if not self.test_process_lifecycle():
                return False
            
            print("\nDeputy smoke test passed!")
            return True
            
        except Exception as e:
            print(f"ERROR: Deputy smoke test failed: {str(e)}")
            return False
            
        finally:
            self.cleanup()


def main():
    """Run smoke test."""
    smoke_test = DeputySmokeTest()
    success = smoke_test.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 