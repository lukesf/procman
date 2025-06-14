import unittest
from unittest.mock import patch, MagicMock
import json
import tempfile
import os
from procman.sheriff.sheriff import Sheriff
from procman.common.process_info import ProcessInfo


class TestSheriff(unittest.TestCase):
    """Test cases for Sheriff class."""
    
    def setUp(self):
        """Set up test cases."""
        self.sheriff = Sheriff()
        self.process_info = ProcessInfo(
            name="test-process",
            command="echo 'test'",
            working_dir="/tmp",
            host="localhost"
        )
    
    @patch('requests.get')
    def test_add_deputy(self, mock_get):
        """Test adding a deputy."""
        # Mock successful health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "hostname": "test-host"
        }
        mock_get.return_value = mock_response
        
        success = self.sheriff.add_deputy("http://localhost:8000")
        
        self.assertTrue(success)
        self.assertEqual(len(self.sheriff.deputies), 1)
        self.assertEqual(
            self.sheriff.deputies["test-host"],
            "http://localhost:8000"
        )
    
    @patch('requests.post')
    def test_start_process(self, mock_post):
        """Test starting a process."""
        # Add deputy
        self.sheriff.deputies["localhost"] = "http://localhost:8000"
        
        # Mock successful process start
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        success = self.sheriff.start_process(self.process_info)
        
        self.assertTrue(success)
        self.assertEqual(len(self.sheriff.processes), 1)
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_stop_process(self, mock_post):
        """Test stopping a process."""
        # Add deputy and process
        self.sheriff.deputies["localhost"] = "http://localhost:8000"
        self.sheriff.processes["test-process"] = self.process_info
        
        # Mock successful process stop
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        success = self.sheriff.stop_process("test-process")
        
        self.assertTrue(success)
        mock_post.assert_called_once()
    
    @patch('requests.get')
    def test_get_deputy_status(self, mock_get):
        """Test getting deputy status."""
        # Add deputies
        self.sheriff.deputies["host1"] = "http://host1:8000"
        self.sheriff.deputies["host2"] = "http://host2:8000"
        
        # Mock responses
        def mock_response(url):
            response = MagicMock()
            if "host1" in url:
                response.status_code = 200
                response.json.return_value = {"status": "healthy"}
            else:
                response.status_code = 500
            return response
        
        mock_get.side_effect = mock_response
        
        status_list = self.sheriff.get_deputy_status()
        
        self.assertEqual(len(status_list), 2)
        self.assertEqual(status_list[0]["status"], "healthy")
        self.assertTrue("unhealthy" in status_list[1]["status"])
    
    @patch('requests.get')
    def test_config_file_operations(self, mock_get):
        """Test saving and loading config files."""
        # Mock successful deputy health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "hostname": "localhost"
        }
        mock_get.return_value = mock_response
        
        # Create a temporary config file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        new_config_file = temp_file.name + ".new"
        
        try:
            config = {
                "deputies": ["http://localhost:8000"],
                "processes": [{
                    "name": "test-process",
                    "command": "echo 'test'",
                    "working_dir": "/tmp",
                    "host": "localhost",
                    "autostart": True,
                    "auto_restart": True
                }]
            }
            json.dump(config, temp_file)
            temp_file.close()
            
            # Test loading config
            self.sheriff.load_config(temp_file.name)
            
            self.assertEqual(len(self.sheriff.deputies), 1)
            self.assertEqual(len(self.sheriff.processes), 1)
            
            process = self.sheriff.processes["test-process"]
            self.assertEqual(process.name, "test-process")
            self.assertTrue(process.autostart)
            self.assertTrue(process.auto_restart)
            
            # Test saving config
            self.sheriff.save_config(new_config_file)
            
            with open(new_config_file, 'r') as f:
                saved_config = json.load(f)
            
            self.assertEqual(len(saved_config["deputies"]), 1)
            self.assertEqual(len(saved_config["processes"]), 1)
            self.assertEqual(
                saved_config["processes"][0]["name"],
                "test-process"
            )
            
        finally:
            # Clean up temporary files
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            if os.path.exists(new_config_file):
                os.unlink(new_config_file)
    
    @patch('requests.post')
    def test_update_process(self, mock_post):
        """Test updating process configuration."""
        # Add deputy and process
        self.sheriff.deputies["localhost"] = "http://localhost:8000"
        self.sheriff.processes["test-process"] = self.process_info
        
        # Create updated process info
        updated_info = ProcessInfo(
            name="test-process",
            command="echo 'updated'",
            working_dir="/tmp",
            host="localhost",
            autostart=True,
            auto_restart=True
        )
        
        # Mock successful process update
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        success = self.sheriff.update_process("test-process", updated_info)
        
        self.assertTrue(success)
        self.assertEqual(
            self.sheriff.processes["test-process"].command,
            "echo 'updated'"
        )
        self.assertTrue(self.sheriff.processes["test-process"].autostart)
        self.assertTrue(self.sheriff.processes["test-process"].auto_restart)


if __name__ == '__main__':
    unittest.main() 