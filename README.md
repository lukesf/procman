# Process Manager (ProcMan)

A distributed process management system consisting of a central Sheriff process manager and distributed Deputy process managers. Inspired by [MIT DGC procman/libbot2-procman](https://github.com/libbot2/libbot2/tree/master/bot2-procman), this Python implementation provides both GUI and CLI interfaces.

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
python3 -m procman sheriff gui

# CLI mode
python3 -m procman sheriff cli
```

### Starting a Deputy
```bash
python3 -m procman deputy --host <deputy_host> --port <deputy_port>
```

## Configuration
Process configurations are stored in JSON format. Example:
```json
{
    "deputies": [
        "http://localhost:8000"
    ],
    "processes": [
        {
            "name": "echoloop",
            "command": "sh -c 'while true; do echo \"hello\"; sleep 1; done'",
            "working_dir": "/tmp",
            "host": "k9.lan",
            "autostart": true,
            "auto_restart": false
        },
        {
            "name": "dateprinter",
            "command": "sh -c 'while true; do date; sleep 5; done'",
            "working_dir": "/tmp",
            "host": "k9.lan",
            "autostart": false,
            "auto_restart": false
        }
    ]
}
```
