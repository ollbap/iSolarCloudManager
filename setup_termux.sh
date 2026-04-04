#!/bin/bash
# Setup script for Termux on Android

set -e

echo "Setting up iSolarCloud Manager for Termux..."

pkg update -y
pkg install -y python
echo "✓ Python installed"
# If the next step fails with "No module named pip", run: pkg install python-pip

python3 -m pip install --upgrade pip -q
python3 -m pip install -r requirements.txt -q
python3 -c "import aiohttp; import pysolarcloud; from zoneinfo import ZoneInfo; ZoneInfo('Europe/Madrid')" || {
    echo "Dependency check failed. Try: python3 -m pip install -r requirements.txt" >&2
    exit 1
}
echo "✓ Dependencies installed (aiohttp, pysolarcloud, tzdata / zoneinfo)"

echo ""
echo "Setup complete! Copy config.example.py to config.py, fill in secrets, then run:"
echo "  ./run_termux.sh"
