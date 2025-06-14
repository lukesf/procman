# Process Manager (ProcMan)

A distributed process management system consisting of a central Sheriff process manager and distributed Deputy process managers.

## Components

### Sheriff
The Sheriff is the central process manager that:
- Loads process configurations from JSON files
- Starts, stops, and restarts processes
- Monitors process statistics (CPU, Memory, etc.)
- Provides both GUI and CLI interfaces
- Communicates with Deputy processes on remote machines

### Deputy
The Deputy is a lightweight process manager that:
- Runs on remote machines
- Receives commands from the Sheriff
- Manages local processes
- Reports process statistics back to the Sheriff

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Unix/macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Sheriff
```bash
# GUI mode
python sheriff.py --gui

# CLI mode
python sheriff.py --cli
```

### Starting a Deputy
```bash
python deputy.py --host <sheriff_host> --port <sheriff_port>
```

## Configuration
Process configurations are stored in JSON format. Example:
```json
{
  "processes": [
    {
      "name": "web_server",
      "command": "python -m http.server 8000",
      "working_dir": "/path/to/web/files",
      "autostart": true
    }
  ]
}
```
