#!/usr/bin/env python3
"""Turn saved database reads into a backup you can keep: every card as JSON and as vault markdown.

The dashboard database can only be read through the claude-artifacts tools (db_list, db_query,
db_get), so a Claude thread saves their results as JSON files first (RESTORE.md, "Export while
you still have access"). This script takes those files. It is tolerant about their shape; it
walks each file and keeps:

  a card      any object with string `id` and `app` and a `status` (the card document itself), or
              an object whose `data` is such a card (then `version` and `path` beside it are kept)
  a meta doc  an object with `path` starting "meta/" and a `data` object

So a list of {path, version, data}, {"documents": [...]}, {"docs": [...]}, one db_get result, a
bare list of card documents, and JSON Lines (one object per line) all work. A card seen twice
keeps the copy with the higher version, then the newer `updated`.

Output folder (never inside this repo: it holds your real cards):
  cards.json                        [{path, version, data}], the full documents: THE backup
  meta.json                         the meta documents found
  Roadmaps/<App>/<ID> <title>.md    each card as a vault file (frontmatter and body)
  index.md                          counts per app and status

The markdown holds the frontmatter fields and the body only. Comments, history and lead_decided
exist only in cards.json, so keep both.

  python3 dashboard/export_cards.py db_dump/*.json --out ~/roadmap-backup
  python3 dashboard/export_cards.py --verify ~/roadmap-backup
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import roadmap_card as rc  # noqa: E402
import sync_vault as sv  # noqa: E402

BAD_IN_NAME = re.compile(r'[\\/:*?"<>|#^\[\]]')


def is_card(o) -> bool:
    return isinstance(o, dict) and isinstance(o.get("id"), str) and isinstance(o.get("app"), str) and "status" in o


def walk(o, cards: list, metas: list) -> None:
    if isinstance(o, list):
        for x in o:
            walk(x, cards, metas)
        return
    if not isinstance(o, dict):
        return
    data = o.get("data")
    path = o.get("path") if isinstance(o.get("path"), str) else ""
    if is_card(data):
        cards.append({"path": path, "version": o.get("version"), "data": data})
        return
    if path.startswith("meta/") and isinstance(data, dict):
        metas.append({"path": path, "version": o.get("version"), "data": data})
        return
    if is_card(o):
        cards.append({"path": "", "version": None, "data": o})
        return
    for v in o.values():
        walk(v, cards, metas)


def load(path: Path):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]  # JSON Lines


def collect(files: list[Path]) -> tuple[list[dict], list[dict]]:
    cards, metas = [], []
    for f in files:
        walk(load(f), cards, metas)
    best: dict[str, dict] = {}
    for c in cards:
        key = c["data"]["id"]
        rank = (c["version"] or 0, str(c["data"].get("updated") or ""))
        if key not in best or rank > (best[key]["version"] or 0, str(best[key]["data"].get("updated") or "")):
            best[key] = c
    out = sorted(best.values(), key=lambda c: (c["data"]["app"], sv.id_num(c["data"]["id"])))
    seen_meta = {m["path"]: m for m in metas}
    return out, sorted(seen_meta.values(), key=lambda m: m["path"])


def file_name(card: dict) -> str:
    src = (card.get("source") or {}).get("file")
    if src:
        return Path(src).name
    title = BAD_IN_NAME.sub("", str(card.get("title") or "")).strip()
    return f"{card['id']} {title}".strip() + ".md"


def app_dir(card: dict) -> str:
    return BAD_IN_NAME.sub("", card["app"]).strip() or "Unknown"


def export(files: list[Path], out: Path) -> int:
    cards, metas = collect(files)
    if not cards:
        print("no card documents found in the input", file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)
    (out / "cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "meta.json").write_text(json.dumps(metas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    counts: dict[str, Counter] = {}
    for c in cards:
        d = c["data"]
        p = out / "Roadmaps" / app_dir(d) / file_name(d)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rc.card_to_md(d), encoding="utf-8")
        counts.setdefault(d["app"], Counter())[str(d.get("status") or "")] += 1
    lines = ["# Card export", "", f"{len(cards)} cards, {len(metas)} meta documents. Full documents: cards.json.", "",
             "| App | " + " | ".join(rc.STATUSES) + " | Total |", "|---|" + "---|" * (len(rc.STATUSES) + 1)]
    for app in sorted(counts):
        n = counts[app]
        other = sum(v for k, v in n.items() if k not in rc.STATUSES)
        lines.append(f"| {app} | " + " | ".join(str(n.get(s, 0)) for s in rc.STATUSES) + f" | {sum(n.values())} |"
                     + (f" ({other} with another status)" if other else ""))
    (out / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for app in sorted(counts):
        print(f"  {app}: {sum(counts[app].values())} cards")
    print(f"wrote {len(cards)} cards to {out} (cards.json, meta.json, Roadmaps/, index.md)")
    return 0


def verify(out: Path) -> int:
    """Re-read every markdown file and compare its fields and body with cards.json."""
    cards = json.loads((out / "cards.json").read_text(encoding="utf-8"))
    bad = 0
    for c in cards:
        d = c["data"]
        p = out / "Roadmaps" / app_dir(d) / file_name(d)
        if not p.exists():
            print(f"MISSING {p}")
            bad += 1
            continue
        fm, _, body = sv.split_card(p.read_text(encoding="utf-8"))
        diffs = [k for k in rc.FM_ORDER if k in d and k != "notion" and not same(k, d[k], fm.get(k))]
        if body != d.get("body", ""):
            diffs.append("body")
        if diffs:
            print(f"DIFFERS {d['id']}: {', '.join(diffs)}")
            bad += 1
    files = len(list((out / "Roadmaps").glob("*/*.md")))
    if files != len(cards):
        print(f"{files} markdown files for {len(cards)} cards")
        bad += 1
    print(f"verify: {len(cards)} cards, {bad} problems")
    return 1 if bad else 0


def same(key: str, doc_value, md_value) -> bool:
    if key == "needs_j":
        return (doc_value is True) == (md_value is True)
    if key == "tags":
        return list(doc_value or []) == list(md_value or [])
    return str(doc_value if doc_value is not None else "") == str(md_value if md_value is not None else "")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path, help="JSON files saved from db_list / db_query / db_get")
    ap.add_argument("--out", type=Path, help="the backup folder to write")
    ap.add_argument("--verify", type=Path, metavar="DIR", help="check an existing backup folder instead")
    args = ap.parse_args(argv)
    if args.verify:
        return verify(args.verify.expanduser())
    if not args.files or not args.out:
        ap.error("give the saved JSON files and --out DIR (or --verify DIR)")
    out = args.out.expanduser().resolve()
    if out == REPO or REPO in out.parents:
        print(f"--out must be outside the repo ({REPO}): the export holds your real cards", file=sys.stderr)
        return 1
    return export([f.expanduser() for f in args.files], out)


if __name__ == "__main__":
    sys.exit(main())
