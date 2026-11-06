"""Separate application gate: laboratory expected failures never grant approval."""
import json
from pathlib import Path
import sys
from scripts.policy import decide

report = json.loads(Path(sys.argv[1]).read_text())
candidate = next(s for s in report["scenarios"] if s["id"] == "candidate")
decision = decide(candidate["checks"])
print(f"Application release gate: {decision}")
raise SystemExit(0 if decision == "approved" else 1)
