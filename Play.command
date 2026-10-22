#!/bin/bash
# Double-click in Finder, or run ./Play.command. The terminal owns the backend.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Install backend/requirements.txt in .venv first (see README.md)."
  exit 1
fi
GODOT="${GODOT_BIN:-}"
if [[ -z "$GODOT" ]]; then
  for candidate in /Applications/Godot.app/Contents/MacOS/Godot "$HOME/Downloads/Godot.app/Contents/MacOS/Godot"; do
    if [[ -x "$candidate" ]]; then GODOT="$candidate"; break; fi
  done
fi
if [[ -z "$GODOT" ]]; then GODOT="$(command -v godot || true)"; fi
if [[ ! -x "$GODOT" ]]; then
  echo "Godot was not found. Set GODOT_BIN to its executable and try again."
  exit 1
fi
set -a
source "$ROOT/config/playtest.env"
set +a
export PYTHONPATH="$ROOT/backend"
cd "$ROOT/backend"
if ! command -v ollama >/dev/null; then echo "Install and start Ollama first (see README.md)."; exit 1; fi
if ! ollama show llama3:willowbrook >/dev/null 2>&1; then
  ollama create llama3:willowbrook -f "$ROOT/config/Modelfile.playtest"
fi
# Refuse to reuse an unknown backend or accidentally launch against its save.
"$PYTHON" - <<'PY'
import socket
with socket.socket() as listener:
    try:
        listener.bind(('127.0.0.1', 8000))
    except OSError:
        raise SystemExit('Port 8000 is already in use. Stop the previous game backend, then run Play.command again.')
PY
"$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
READY=false
for ((attempt=0; attempt<100; attempt++)); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend startup failed; see the error above."
    exit 1
  fi
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then READY=true; break; fi
  sleep 0.1
done
if [[ "$READY" != true ]]; then echo "Backend startup timed out."; exit 1; fi
echo "Llama 3 playtest ready. Close the game normally to save and stop the backend."
"$GODOT" --headless --path "$ROOT/frontend/godot" --editor --import
"$GODOT" --path "$ROOT/frontend/godot"
