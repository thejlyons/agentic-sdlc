#!/usr/bin/env python3
"""Re-copy the live process files into this repo, sanitised.

The live system runs from the owner's Claude Code folders. This script copies each live file to its
place here, applies the sanitising rules, stamps a header, runs the forbidden-pattern scan and
prints what changed, so the lead can read the diff and commit it.

The list of live files, the replace map and the per-file patches are in a PRIVATE config, because
they contain the very names they remove. Its path is $SDLC_SYNC_PRIVATE (default
~/.claude/lead/sdlc-showcase/sync.private.json); sync/private.example.json shows the shape.

Per source file, in this order:
  1. patches   exact old -> new strings for that file. A patch whose old text is missing FAILS the
               run: the live file changed where the public version differs, so a person must look.
  2. replace   ordered regex -> replacement pairs applied to every file (names, ids, paths).
  3. header    one line saying it is the live version as of the day its content last changed.
Kinds: "copy" (the above), "retro" (the retro table, newest first), "extract" (part of a live file).
After the copies, the private config's "collectors" run: they refresh data/*.tsv (merged PRs, reviewer
runs) from the private app repos and the lead's transcripts, for scripts/metrics.py.

  python3 scripts/sync.py            write, scan, print the diff summary
  python3 scripts/sync.py --check    write nothing; exit 1 if the repo is behind the live files
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = Path(os.environ.get("SDLC_SYNC_PRIVATE", "~/.claude/lead/sdlc-showcase/sync.private.json")).expanduser()
TODAY = dt.date.today().isoformat()
STAMP = "Live version as of "
NOTE = {
    "prose": ("sanitised by scripts/sync.py. App names (FieldApp, StudyApp), card ids (FLD-123), `$TOKENS` and "
              "the machine's numbers are example values: at run time the real ones come from "
              "`~/.claude/lead/config.json` (config/SCHEMA.md) and win wherever they differ."),
    "code": "sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.",
    "doc": "sanitised by scripts/sync.py; app names and ids are the example config's.",
}


def header(dest: str, style: str, date: str) -> str:
    text = f"{STAMP}{date}, {NOTE[style]}"
    ext = Path(dest).suffix
    if ext == ".md":
        return f"> {text}\n\n"
    if ext == ".js":
        return f"// {text}\n"
    if ext == ".html":
        return f"<!-- {text} -->\n"
    return f"# {text}\n"


def place_header(dest: str, body: str, head: str) -> str:
    """After YAML frontmatter, a shebang or a doctype; otherwise first."""
    if body.startswith("---\n"):
        end = body.index("\n---\n", 4) + 5
        return body[:end] + "\n" + head + body[end:].lstrip("\n")
    first, _, rest = body.partition("\n")
    if first.startswith("#!") or first.lower().startswith("<!doctype"):
        return first + "\n" + head + rest
    return head + body


def strip_header(text: str) -> tuple[str, str]:
    """(text without its stamp line, the stamp's date or '')."""
    m = re.search(r"^(?:> |// |# |<!-- )" + re.escape(STAMP) + r"(\d{4}-\d{2}-\d{2}),[^\n]*\n\n?", text, re.M)
    if not m:
        return text, ""
    return text[:m.start()] + text[m.end():], m.group(1)


def sanitise(text: str, cfg: dict, dest: str) -> str:
    for old, new in cfg.get("patches", {}).get(dest, []):
        if old not in text:
            raise SystemExit(f"PATCH MISSED in {dest}: the live file no longer contains\n  {old[:160]!r}\n"
                             "Read the live change and update the patch in the private config.")
        text = text.replace(old, new)
    for pat, rep in cfg["replace"]:
        text = re.sub(pat, rep, text)
    return text


def retro(text: str) -> str:
    rows = [l for l in text.split("\n") if re.match(r"\| \d{4}-\d{2}-\d{2} \|", l)]
    out = ["# Retro log", "",
           "One dated line per card or incident: what worked, what broke, the lesson. Kept by the lead session",
           "(skill `lead-loop`, section Retro), newest first here. About every ten cards the durable lessons are",
           "folded into the skills and agents; CHANGELOG.md records when. Card ids and app names are the example",
           "config's; PR numbers are those of the private app repos.", "",
           "| Date | Card / event | Worked | Broke | Lesson |", "|---|---|---|---|---|"]
    return "\n".join(out + rows[::-1]) + "\n"


def extract(text: str, spec: dict) -> str:
    start = text.index(spec["from"]) if spec.get("from") else 0
    end = text.index(spec["until"], start) if spec.get("until") else len(text)
    return spec.get("prefix", "") + text[start:end].rstrip("\n") + "\n"


def build(cfg: dict) -> dict[str, str]:
    out = {}
    for s in cfg["sources"]:
        src, dest, kind = Path(s["src"]).expanduser(), s["dest"], s.get("kind", "copy")
        raw = src.read_text(encoding="utf-8")
        if kind == "extract":
            raw = extract(raw, s)
        body = sanitise(raw, cfg, dest)
        if kind == "retro":
            body = retro(body)
        old_path = ROOT / dest
        date = TODAY
        if old_path.exists():
            old_body, old_date = strip_header(old_path.read_text(encoding="utf-8"))
            if old_date and old_body == strip_header(place_header(dest, body, header(dest, s.get("style", "prose"), TODAY)))[0]:
                date = old_date
        out[dest] = place_header(dest, body, header(dest, s.get("style", "prose"), date))
    return out


def main() -> int:
    check = "--check" in sys.argv
    if not PRIVATE.exists():
        print(f"No private sync config at {PRIVATE}. Only the owner's machine can sync; "
              "see sync/private.example.json. Running the scan only.")
        return subprocess.call([sys.executable, str(ROOT / "scripts" / "scan.py")])
    cfg = json.loads(PRIVATE.read_text(encoding="utf-8"))
    files = build(cfg)
    changed = [d for d, t in files.items() if not (ROOT / d).exists() or (ROOT / d).read_text(encoding="utf-8") != t]
    if check:
        for d in changed:
            print("behind:", d)
        print(f"{len(changed)} of {len(files)} synced files differ from the live sources")
        return 1 if changed else 0
    for d in changed:
        p = ROOT / d
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(files[d], encoding="utf-8")
        if p.suffix in (".sh", ".py") and files[d].startswith("#!"):
            p.chmod(0o755)
    for cmd in cfg.get("collectors", []):  # private scripts that refresh data/*.tsv from the private repos
        subprocess.check_call([os.path.expanduser(a).replace("{root}", str(ROOT)) for a in cmd])
    state = {"last_synced": TODAY, "files": sorted(files)}
    (ROOT / "sync" / "last-synced.json").write_text(json.dumps(state, indent=2) + "\n")
    readme = ROOT / "README.md"
    if readme.exists():
        t = readme.read_text(encoding="utf-8")
        t2 = re.sub(r"(Last synced with the live system: )\d{4}-\d{2}-\d{2}", r"\g<1>" + TODAY, t)
        if t2 != t:
            readme.write_text(t2, encoding="utf-8")
    print(f"synced {len(files)} files, {len(changed)} changed:")
    for d in changed:
        print("  ", d)
    subprocess.call(["git", "-C", str(ROOT), "--no-pager", "diff", "--stat"])
    subprocess.call(["git", "-C", str(ROOT), "status", "--short"])
    rc = subprocess.call([sys.executable, str(ROOT / "scripts" / "scan.py")])
    if rc:
        print("SCAN FAILED: fix the replace map or the patches, run again, and do not commit until it passes.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
