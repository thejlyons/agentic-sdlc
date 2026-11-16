#!/usr/bin/env python3
"""Forbidden-pattern scan for this repo.

Reads sync/forbidden.json (generic patterns: emails, home paths, UUIDs, tokens, ...) and, when it
exists, a private file with the real app and project names (path in $SDLC_SYNC_PRIVATE, default
~/.claude/lead/sdlc-showcase/sync.private.json; never committed). Every hit that is not covered by
an `allow` entry is printed as path:line and the run exits 1.

  python3 scripts/scan.py            scan the working tree (tracked and untracked, not ignored)
  python3 scripts/scan.py --report   also print the allowed hits with their reasons
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = Path(os.environ.get("SDLC_SYNC_PRIVATE", "~/.claude/lead/sdlc-showcase/sync.private.json")).expanduser()
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip"}


def files() -> list[Path]:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-co", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout.split("\n")
        return [ROOT / p for p in out if p and (ROOT / p).is_file()]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def load() -> tuple[list[dict], list[dict], bool]:
    cfg = json.loads((ROOT / "sync" / "forbidden.json").read_text())
    forbidden, allow, private = list(cfg["forbidden"]), list(cfg.get("allow", [])), False
    if PRIVATE.exists():
        p = json.loads(PRIVATE.read_text())
        forbidden += p.get("forbidden_private", [])
        allow += p.get("allow_private", [])
        private = True
    return forbidden, allow, private


def scan(report: bool = False) -> int:
    forbidden, allow, private = load()
    pats = [(f["name"], re.compile(f["regex"])) for f in forbidden]
    allows = [(a["path"], re.compile(a["regex"]), a["reason"]) for a in allow]
    hits, allowed = [], []
    for path in files():
        if path.suffix.lower() in BINARY:
            continue
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            hits.append((rel, 0, "not UTF-8 text", ""))
            continue
        for n, line in enumerate(text.split("\n"), 1):
            for name, pat in pats:
                for m in pat.finditer(line):
                    reason = next((r for p, rx, r in allows
                                   if re.fullmatch(p.replace("*", ".*"), rel) and rx.search(line)), None)
                    (allowed if reason else hits).append((rel, n, name, m.group(0), reason))
    if report:
        for rel, n, name, what, reason in allowed:
            print(f"allowed  {rel}:{n}  {name}: {what!r}  ({reason})")
    for h in hits:
        print(f"FORBIDDEN  {h[0]}:{h[1]}  {h[2]}: {h[3]!r}")
    print(f"scan: {len(hits)} forbidden, {len(allowed)} allowed, "
          f"{'generic + private' if private else 'generic'} patterns")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(scan("--report" in sys.argv))
