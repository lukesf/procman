# ProcMan Development Container

This directory contains the configuration for a development container that provides a consistent development environment for the ProcMan project.

## What's Included

- **Ubuntu 22.04** base image
- **Python 3.11** with virtual environment
- **PyQt5** for GUI development
- **Development tools**: black, isort, flake8, pylint, pytest
- **Pre-commit hooks** for code quality
- **Virtual display** (Xvfb) for GUI testing

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Using the Dev Container

1. **Open in VS Code**: Open the project folder in VS Code
2. **Reopen in Container**: When prompted, click "Reopen in Container" or use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"
3. **Wait for Setup**: The container will build and run the setup script automatically
4. **Start Developing**: Once setup is complete, you can start coding!

### Manual Setup (if needed)

If you need to run the setup manually:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-qt5 python3-pyqt5.qtcore python3-pyqt5.qtgui python3-pyqt5.qtwidgets xvfb

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install -e .

# Install development tools
pip install black isort flake8 pylint pytest-cov pytest-mock pre-commit

# Set up pre-commit hooks
pre-commit install
```

## Running Tests

### All Tests
```bash
./run_tests_dev.sh
```

### Unit Tests Only
```bash
source venv/bin/activate
python -m pytest tests/ -v --cov=procman
```

### Smoke Tests
```bash
source venv/bin/activate
python tests/smoke_test_deputy.py
python tests/smoke_test_cli.py
```

### GUI Tests (with virtual display)
```bash
# Start virtual display
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99

# Run tests
source venv/bin/activate
python -m pytest tests/ -v -m "gui"
```

## Code Quality

The devcontainer includes several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **pylint**: Advanced linting
- **pre-commit**: Git hooks for quality checks

### Formatting Code
```bash
# Format with black
black procman/ tests/

# Sort imports
isort procman/ tests/
```

### Running Linters
```bash
# Run flake8
flake8 procman/ tests/

# Run pylint
pylint procman/ tests/
```

## Troubleshooting

### PyQt5 Issues
If you encounter PyQt5-related errors:
1. Ensure the virtual display is running: `Xvfb :99 -screen 0 1024x768x24 &`
2. Set the DISPLAY variable: `export DISPLAY=:99`
3. Check that PyQt5 packages are installed: `dpkg -l | grep pyqt5`

### Permission Issues
If you encounter permission issues:
1. Ensure you're running as the `vscode` user in the container
2. Check file permissions: `ls -la`
3. Use `sudo` for system-level operations if needed

### Virtual Environment Issues
If the virtual environment isn't working:
1. Activate manually: `source venv/bin/activate`
2. Reinstall: `rm -rf venv && python3 -m venv venv`
3. Reinstall dependencies: `pip install -r requirements.txt`

## Environment Variables

The following environment variables are set automatically:
- `PYTHONPATH`: Points to the project root
- `DISPLAY`: Set to `:99` for virtual display
- `VIRTUAL_ENV`: Points to the Python virtual environment

## Contributing

When contributing to this project:
1. Use the devcontainer for consistent development
2. Run tests before committing: `./run_tests_dev.sh`
3. Ensure code passes all quality checks
4. Use pre-commit hooks to maintain quality
