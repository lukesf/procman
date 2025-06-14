#!/usr/bin/env python3
"""Smoke test for procman CLI interface."""

import os
import sys
import time
import json
import signal
import subprocess
import requests
import tempfile
from typing import List, Optional, Dict, Tuple


class CLISmokeTest:
    """CLI smoke test runner."""
    
    def __init__(self):
        """Initialize smoke test."""
        self.deputy_process: Optional[subprocess.Popen] = None
        self.deputy_url = "http://localhost:8000"
        self.config_file = "smoke_test_cli_config.json"
        self.output_file = "cli_output.txt"
    
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
    
    def run_cli_command(self, command: List[str]) -> Tuple[int, str, str]:
        """Run a Sheriff CLI command and return exit code and output."""
        process = subprocess.Popen(
            ["python", "-m", "procman.sheriff.cli"] + command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    
    def check_deputy_health(self) -> bool:
        """Check Deputy health."""
        print("Checking Deputy health...")
        try:
            response = requests.get(f"{self.deputy_url}/health")
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def test_deputy_management(self) -> bool:
        """Test deputy management commands."""
        print("\nTesting deputy management...")
        
        # Add deputy
        code, stdout, stderr = self.run_cli_command(["add-deputy", self.deputy_url])
        if code != 0:
            print(f"ERROR: Failed to add deputy: {stderr}")
            return False
        print("Successfully added deputy")
        
        # Check deputy status (retry a few times)
        for _ in range(3):
            code, stdout, stderr = self.run_cli_command(["status"])
            if code == 0:
                if "localhost" in stdout:  # Check for localhost since we're running locally
                    print("Successfully checked deputy status")
                    return True
                print(f"Deputy status output: {stdout}")
            time.sleep(2)
        
        print(f"ERROR: Deputy status check failed after retries")
        print(f"Exit code: {code}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        return False
    
    def test_process_management(self) -> bool:
        """Test process management commands."""
        print("\nTesting process management...")
        
        # Load config
        code, stdout, stderr = self.run_cli_command(["load-config", self.config_file])
        if code != 0:
            print(f"ERROR: Failed to load config: {stderr}")
            return False
        print("Successfully loaded config")
        
        # Check process status
        time.sleep(2)  # Wait for process to start
        code, stdout, stderr = self.run_cli_command(["status"])
        if code != 0 or "counter" not in stdout:
            print(f"ERROR: Process status check failed: {stderr}")
            return False
        print("Successfully checked process status")
        
        # Stop process
        code, stdout, stderr = self.run_cli_command(["stop-process", "counter"])
        if code != 0:
            print(f"ERROR: Failed to stop process: {stderr}")
            return False
        print("Successfully stopped process")
        
        # Start process
        code, stdout, stderr = self.run_cli_command(["start-process", "counter"])
        if code != 0:
            print(f"ERROR: Failed to start process: {stderr}")
            return False
        print("Successfully started process")
        
        # Restart process
        code, stdout, stderr = self.run_cli_command(["restart-process", "counter"])
        if code != 0:
            print(f"ERROR: Failed to restart process: {stderr}")
            return False
        print("Successfully restarted process")
        
        return True
    
    def cleanup(self):
        """Clean up test environment."""
        print("\nCleaning up...")
        
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
            
            # Test deputy management
            if not self.test_deputy_management():
                return False
            
            # Test process management
            if not self.test_process_management():
                return False
            
            print("\nCLI smoke test passed!")
            return True
            
        except Exception as e:
            print(f"ERROR: CLI smoke test failed: {str(e)}")
            return False
            
        finally:
            self.cleanup()


def main():
    """Run smoke test."""
    smoke_test = CLISmokeTest()
    success = smoke_test.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 