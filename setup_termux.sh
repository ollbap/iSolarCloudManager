#!/bin/bash
# Setup script for Termux on Android

set -e

echo "Setting up iSolarCloud Manager for Termux..."

pkg update -y
pkg install -y python
echo "✓ Python installed"

pip install -r requirements.txt -q
echo "✓ Dependencies installed"

echo ""
echo "Setup complete! Copy config.example.py to config.py, fill in secrets, then run:"
echo "  ./run_termux.sh"
