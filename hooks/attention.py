#!/usr/bin/env python3
# Live version as of 2026-11-16, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
"""Notification hook: fallback when a session (lead or background worker) waits on J.

Remote Control push is the main ping. This records the wait in
~/.claude/lead/attention.jsonl (read by /back-to-work and the lead's worker checks)
and shows a desktop notification on the Mac. Nothing leaves the machine.
"""
import json, os, subprocess, sys, time

WATCH = {"permission_prompt", "idle_prompt", "agent_needs_input", "elicitation_dialog"}
try:
    d = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
kind = d.get("notification_type", "")
if kind not in WATCH:
    sys.exit(0)
msg = (d.get("message") or "Needs your attention")[:300]
rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "type": kind, "session": d.get("session_id", ""),
       "cwd": d.get("cwd", ""), "message": msg}
path = os.path.expanduser("~/.claude/lead/attention.jsonl")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "a") as f:
    f.write(json.dumps(rec) + "\n")
where = os.path.basename(rec["cwd"]) or "claude"
try:
    subprocess.run(["osascript", "-e", "on run argv", "-e",
                    "display notification (item 1 of argv) with title (item 2 of argv)", "-e", "end run",
                    msg, "Claude waiting: " + where], timeout=5, capture_output=True)
except Exception:
    pass
