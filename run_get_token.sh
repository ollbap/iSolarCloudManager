#!/bin/bash
# Run OAuth helper on desktop (Linux/macOS) — same pattern as run.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source venv/bin/activate
python3 get_access_token.py "$@"
