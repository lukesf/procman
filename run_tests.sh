#!/bin/bash

# Run unit tests with coverage
echo "Running unit tests..."
python -m pytest tests/ -v --cov=procman

# Run smoke tests
echo -e "\nRunning GUI smoke test..."
python tests/smoke_test.py

echo -e "\nRunning CLI smoke test..."
python tests/smoke_test_cli.py 

echo -e "\nRunning Deputy smoke test..."
python tests/smoke_test_deputy.py