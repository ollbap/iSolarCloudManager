#!/bin/bash
# Run only current generation/consumption (no 7-day table) — desktop

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source venv/bin/activate
python3 isolar_report.py --now-only
