#!/bin/bash
# MASU Phishing Kit — launcher
# Auto-activates venv, passes all args to masu-phish.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"

if [ ! -d "$VENV" ]; then
  echo "[*] Creating virtual environment..."
  python -m venv "$VENV"
  echo "[*] Installing dependencies..."
  "$VENV/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q
  echo "[+] Setup complete."
fi

source "$VENV/bin/activate"
python "$SCRIPT_DIR/masu-phish.py" "$@"
