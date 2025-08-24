#!/bin/bash
set -e

echo "🚀 Setting up ProcMan development environment..."

# Update package lists
echo "📦 Updating package lists..."
apt-get update

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt-get install -y \
    python3-pip \
    python3-venv \
    python3-qt5 \
    python3-pyqt5.qtcore \
    python3-pyqt5.qtgui \
    python3-pyqt5.qtwidgets \
    xvfb \
    curl \
    wget \
    build-essential \
    git

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv /workspaces/procman/venv
source /workspaces/procman/venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
cd /workspaces/procman
pip install -r requirements.txt
pip install -e .

# Install development tools
echo "🛠️ Installing development tools..."
pip install \
    black \
    isort \
    flake8 \
    pylint \
    pytest-cov \
    pytest-mock

# Set up pre-commit hooks
echo "🔒 Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install

# Create a test runner script
echo "📝 Creating test runner script..."
cat > /workspaces/procman/run_tests_dev.sh << 'EOF'
#!/bin/bash
cd /workspaces/procman
source venv/bin/activate

echo "🧪 Running tests in development environment..."

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/ -v --cov=procman --cov-report=term-missing

# Run smoke tests
echo -e "\nRunning Deputy smoke test..."
python tests/smoke_test_deputy.py

echo -e "\nRunning CLI smoke test..."
python tests/smoke_test_cli.py

echo -e "\n✅ All tests completed!"
EOF

chmod +x /workspaces/procman/run_tests_dev.sh

# Set up environment variables
echo "🌍 Setting up environment variables..."
echo 'export PYTHONPATH="/workspaces/procman:$PYTHONPATH"' >> ~/.bashrc
echo 'export DISPLAY=":99"' >> ~/.bashrc

echo "🎉 ProcMan development environment setup complete!"
echo ""
echo "To run tests: ./run_tests_dev.sh"
echo "To activate virtual environment: source venv/bin/activate"
echo "To start virtual display: Xvfb :99 -screen 0 1024x768x24 &"
