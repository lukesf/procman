import unittest
from unittest.mock import patch, MagicMock
import psutil
import subprocess
from procman.deputy.deputy import Deputy
from procman.common.process_info import ProcessInfo


class TestDeputy(unittest.TestCase):
    """Test cases for Deputy class."""
    
    def setUp(self):
        """Set up test cases."""
        self.deputy = Deputy(host="localhost", port=8000)
        self.process_info = ProcessInfo(
            name="test-process",
            command="echo 'test'",
            working_dir="/tmp",
            host="localhost"
        )
    
    @patch('subprocess.Popen')
    def test_start_process(self, mock_popen):
        """Test starting a process."""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        # Start process
        success = self.deputy.start_process(self.process_info)
        
        self.assertTrue(success)
        self.assertEqual(self.process_info.pid, 1234)
        self.assertEqual(self.process_info.status, "running")
        self.assertIsNotNone(self.process_info.start_time)
        mock_popen.assert_called_once()
    
    @patch('subprocess.Popen')
    def test_start_process_failure(self, mock_popen):
        """Test process start failure."""
        # Mock process creation failure
        mock_popen.side_effect = Exception("Failed to start")
        
        # Try to start process
        success = self.deputy.start_process(self.process_info)
        
        self.assertFalse(success)
        self.assertEqual(self.process_info.status, "error: Failed to start")
        self.assertIsNone(self.process_info.pid)
    
    @patch('os.killpg')
    @patch('os.getpgid')
    @patch('subprocess.Popen')
    def test_stop_process(self, mock_popen, mock_getpgid, mock_killpg):
        """Test stopping a process."""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        # Mock process group ID
        mock_getpgid.return_value = 1234
        
        # Start and then stop process
        self.deputy.start_process(self.process_info)
        self.deputy._process_handles["test-process"] = mock_process
        success = self.deputy.stop_process("test-process")
        
        self.assertTrue(success)
        self.assertEqual(self.process_info.status, "stopped")
        self.assertIsNone(self.process_info.pid)
        mock_killpg.assert_called_once()
    
    @patch('select.select')
    @patch('psutil.Process')
    @patch('subprocess.Popen')
    def test_process_output_capture(self, mock_popen, mock_psutil_process, mock_select):
        """Test process output capture."""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_process.poll.side_effect = [None, None, 0]  # Return None twice, then 0 to simulate process exit
        mock_popen.return_value = mock_process

        # Mock psutil process
        mock_psutil = MagicMock()
        mock_psutil.cpu_percent.return_value = 10.5
        mock_psutil.memory_percent.return_value = 5.2
        mock_psutil_process.return_value = mock_psutil

        # Create temporary files for testing
        import tempfile
        stdout_file = tempfile.NamedTemporaryFile(mode='w+', prefix="test-stdout-")
        stderr_file = tempfile.NamedTemporaryFile(mode='w+', prefix="test-stderr-")

        # Write test output
        stdout_file.write("test output\n")
        stderr_file.write("test error\n")
        stdout_file.flush()
        stderr_file.flush()
        stdout_file.seek(0)
        stderr_file.seek(0)

        # Start process
        self.deputy.start_process(self.process_info)

        # Simulate output capture
        import threading
        capture_thread = threading.Thread(
            target=self.deputy._capture_output,
            args=("test-process", mock_process, stdout_file, stderr_file)
        )
        capture_thread.start()

        # Wait for output to be processed
        import time
        time.sleep(0.5)

        # Check captured output
        self.assertEqual(list(self.process_info.stdout_buffer), ["test output"])
        self.assertEqual(list(self.process_info.stderr_buffer), ["test error"])

        # Clean up
        stdout_file.close()
        stderr_file.close()
    
    @patch('select.select')
    @patch('subprocess.Popen')
    def test_auto_restart(self, mock_popen, mock_select):
        """Test auto-restart functionality."""
        # Mock first process
        mock_process1 = MagicMock()
        mock_process1.pid = 1234
        mock_process1.poll.side_effect = [None, 1]  # Process exits with code 1
        mock_process1.communicate.return_value = ("", "")

        # Mock second process (after restart)
        mock_process2 = MagicMock()
        mock_process2.pid = 1235
        mock_process2.poll.return_value = None

        # Set up process creation sequence
        mock_popen.side_effect = [mock_process1, mock_process2]

        # Create temporary files for testing
        import tempfile
        stdout_file1 = tempfile.NamedTemporaryFile(mode='w+', prefix="test-stdout1-")
        stderr_file1 = tempfile.NamedTemporaryFile(mode='w+', prefix="test-stderr1-")

        # Enable auto-restart
        self.process_info.auto_restart = True

        # Start process
        self.deputy.start_process(self.process_info)

        # Simulate process exit and auto-restart
        self.deputy._capture_output("test-process", mock_process1, stdout_file1, stderr_file1)

        # Verify auto-restart was called with correct arguments
        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0], "echo 'test'")
        self.assertEqual(kwargs['cwd'], '/tmp')
        self.assertEqual(kwargs['start_new_session'], True)
        self.assertEqual(kwargs['shell'], True)
        self.assertEqual(kwargs['executable'], '/bin/bash')

        # Clean up
        stdout_file1.close()
        stderr_file1.close()


if __name__ == '__main__':
    unittest.main() 