#!/bin/bash
# Setup script for desktop environments (Linux/macOS)

set -e

echo "Setting up iSolarCloud Manager..."

python3 -m venv venv
echo "✓ Virtual environment created"

source venv/bin/activate
python3 -m pip install --upgrade pip -q
python3 -m pip install -r requirements.txt -q
echo "✓ Dependencies installed"

echo ""
echo "Setup complete! Copy config.example.py to config.py, fill in secrets, then run:"
echo "  ./run.sh"
