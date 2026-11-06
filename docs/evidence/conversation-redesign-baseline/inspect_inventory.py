"""Read-only T01 inspection; uses no app imports, database, provider or network.

Run from repository root with .venv/bin/python <this file>. Outputs stay here.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
commands = [
    ["git", "rev-parse", "HEAD"],
    ["git", "branch", "--show-current"],
    ["git", "status", "--short"],
    [str(ROOT / ".venv/bin/python"), "--version"],
    ["/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot", "--version"],
    ["rg", "-n", "max_length|min_length|maxLength|maxItems|max_tokens|timeout|limit\\(|\\[:[0-9]|max_dialogue|memory_top_k|candidate_count", "backend/app", "frontend/godot/scripts/chat_window.gd"],
    ["rg", "-n", "commit\\(|flush\\(|revision|inventory =|\\.phase =|\\.status =|\\.state =|game_id=|timeline_id=", "backend/app"],
    ["rg", "--files", "backend/tests", "frontend/godot/tests"],
]
records = []
for index, command in enumerate(commands):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    name = f"inspection-{index:02d}.txt"
    (OUT / name).write_text(result.stdout + result.stderr)
    records.append({"argv": command, "exit_code": result.returncode, "output": name})
paths = [
    "backend/app/api/routes/chat.py", "backend/app/schemas/chat.py",
    "backend/app/services/pipeline.py", "backend/app/services/context/builder.py",
    "backend/app/services/llm/openai_compatible.py", "backend/app/services/validation/service.py",
    "backend/app/services/context/grounding.py", "backend/app/services/craftsman.py",
    "backend/app/services/gatherer.py", "backend/app/services/craftsman_intent.py",
    "backend/app/services/quests/bow.py", "backend/app/services/quests/ship_repair.py",
    "backend/app/services/state/service.py", "backend/app/services/opening.py",
    "backend/app/services/memory/provenance.py", "backend/app/services/memory/service.py",
    "backend/app/services/memory/reindex.py", "backend/app/api/routes/memory.py",
    "backend/app/models/memory.py", "backend/app/database/seed.py",
    "backend/app/api/routes/quests.py", "backend/app/api/routes/world.py",
    "backend/app/dialogue/compose.py", "frontend/godot/scripts/chat_window.gd",
    "frontend/godot/scripts/main.gd", "frontend/godot/scripts/craftsman_gateway.gd",
    "frontend/godot/scripts/gatherer_gateway.gd",
]
with (OUT / "source-snapshot.txt").open("w") as stream:
    for name in paths:
        stream.write(f"\nFILE {name}\n")
        for number, line in enumerate((ROOT / name).read_text().splitlines(), 1):
            stream.write(f"{number}: {line}\n")
(OUT / "inspection-manifest.json").write_text(json.dumps({
    "task": "baseline/T01", "captured_at": datetime.now(timezone.utc).isoformat(),
    "cwd": str(ROOT), "python": sys.executable,
    "platform": platform.platform(), "commands": records,
    "source_snapshot": paths, "method": "static source inspection; no application import",
}, indent=2) + "\n")
print(f"Captured {len(commands)} commands and {len(paths)} source files")
sys.exit(0 if all(item["exit_code"] == 0 for item in records) else 1)
