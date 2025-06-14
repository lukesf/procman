import unittest
from procman.common.process_info import ProcessInfo
import time


class TestProcessInfo(unittest.TestCase):
    """Test cases for ProcessInfo class."""
    
    def setUp(self):
        """Set up test cases."""
        self.process = ProcessInfo(
            name="test-process",
            command="echo 'test'",
            working_dir="/tmp",
            host="localhost"
        )
    
    def test_init(self):
        """Test ProcessInfo initialization."""
        self.assertEqual(self.process.name, "test-process")
        self.assertEqual(self.process.command, "echo 'test'")
        self.assertEqual(self.process.working_dir, "/tmp")
        self.assertEqual(self.process.host, "localhost")
        self.assertFalse(self.process.autostart)
        self.assertFalse(self.process.auto_restart)
        self.assertIsNone(self.process.pid)
        self.assertEqual(self.process.cpu_percent, 0.0)
        self.assertEqual(self.process.memory_percent, 0.0)
        self.assertEqual(self.process.status, "stopped")
        self.assertIsNone(self.process.start_time)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        self.process.pid = 1234
        self.process.cpu_percent = 10.5
        self.process.memory_percent = 5.2
        self.process.status = "running"
        self.process.start_time = time.time()
        self.process.autostart = True
        self.process.auto_restart = True
        
        data = self.process.to_dict()
        
        self.assertEqual(data["name"], "test-process")
        self.assertEqual(data["command"], "echo 'test'")
        self.assertEqual(data["working_dir"], "/tmp")
        self.assertEqual(data["host"], "localhost")
        self.assertTrue(data["autostart"])
        self.assertTrue(data["auto_restart"])
        self.assertEqual(data["pid"], 1234)
        self.assertEqual(data["cpu_percent"], 10.5)
        self.assertEqual(data["memory_percent"], 5.2)
        self.assertEqual(data["status"], "running")
        self.assertIsNotNone(data["start_time"])
        self.assertGreaterEqual(data["uptime"], 0)
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "name": "test-process",
            "command": "echo 'test'",
            "working_dir": "/tmp",
            "host": "localhost",
            "autostart": True,
            "auto_restart": True,
            "pid": 1234,
            "cpu_percent": 10.5,
            "memory_percent": 5.2,
            "status": "running",
            "start_time": time.time(),
            "stdout": ["line1", "line2"],
            "stderr": ["error1"],
            "last_stdout_pos": 2,
            "last_stderr_pos": 1
        }
        
        process = ProcessInfo.from_dict(data)
        
        self.assertEqual(process.name, "test-process")
        self.assertEqual(process.command, "echo 'test'")
        self.assertEqual(process.working_dir, "/tmp")
        self.assertEqual(process.host, "localhost")
        self.assertTrue(process.autostart)
        self.assertTrue(process.auto_restart)
        self.assertEqual(process.pid, 1234)
        self.assertEqual(process.cpu_percent, 10.5)
        self.assertEqual(process.memory_percent, 5.2)
        self.assertEqual(process.status, "running")
        self.assertIsNotNone(process.start_time)
        self.assertEqual(list(process.stdout_buffer), ["line1", "line2"])
        self.assertEqual(list(process.stderr_buffer), ["error1"])
        self.assertEqual(process.last_stdout_pos, 2)
        self.assertEqual(process.last_stderr_pos, 1)
    
    def test_add_output(self):
        """Test output buffer management."""
        self.process.add_output(stdout="line1")
        self.process.add_output(stderr="error1")
        self.process.add_output(stdout="line2")
        
        self.assertEqual(list(self.process.stdout_buffer), ["line1", "line2"])
        self.assertEqual(list(self.process.stderr_buffer), ["error1"])


if __name__ == '__main__':
    unittest.main() 