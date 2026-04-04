#!/bin/bash
# Run only current generation/consumption (no 7-day table) — Termux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Keep the session readable when launched from Termux:Widget (window often closes on exit).
_pause_termux_exit() {
  echo ""
  if [ -t 0 ]; then
    read -r -p "Press Enter to close... " || true
  else
    sleep 30
  fi
}
trap _pause_termux_exit EXIT

python3 isolar_report.py --now-only
