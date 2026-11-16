#!/usr/bin/env python3
"""Check that every relative markdown link in the repo points at a file that exists (and, for #anchors
into markdown files, at a heading that exists). External http(s) links are not fetched."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")


def slug(h: str) -> str:
    h = re.sub(r"[`*_]", "", h.strip().lower())
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", h))


def anchors(p: Path) -> set:
    text = re.sub(r"```.*?```", "", p.read_text(encoding="utf-8"), flags=re.S)
    return {slug(m.group(1)) for m in re.finditer(r"^#+\s+(.*)$", text, re.M)}


files = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-co", "--exclude-standard", "*.md"],
                       capture_output=True, text=True).stdout.split()
bad = 0
for rel in files:
    p = ROOT / rel
    if "example-vault" in rel or not p.is_file():
        continue
    text = re.sub(r"```.*?```", "", p.read_text(encoding="utf-8"), flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    for target in LINK.findall(text):
        if re.match(r"[a-z]+:", target) or target.startswith("<"):
            continue
        path, _, frag = target.partition("#")
        dest = (p.parent / path).resolve() if path else p
        if not dest.exists():
            print(f"BROKEN  {rel}: {target}")
            bad += 1
        elif frag and dest.suffix == ".md" and frag not in anchors(dest):
            print(f"NO ANCHOR  {rel}: {target}")
            bad += 1
print(f"linkcheck: {len(files)} markdown files, {bad} broken")
sys.exit(1 if bad else 0)
