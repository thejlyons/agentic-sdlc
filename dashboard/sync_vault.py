#!/usr/bin/env python3
# Live version as of 2026-11-16, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
"""Mirror the vault's roadmap cards into the studio roadmap artifact.

The vault (Roadmaps/<App>/<ID> <title>.md) stays the source of truth for every app except the
DB_APPS below (FieldApp since 2026-11-05, StudyApp since 2026-11-06, AppC since 2026-11-11),
whose cards live in the
artifact's database (see ROADMAP-DB.md and roadmap_card.py). This script only reads the vault
(files and `git log`); it never writes to it.

It writes, next to itself:
  out/mirror.js   window.ROADMAP_MIRROR = {synced_at, vault_commit, vault_commit_at, cards: [...]}
                  One row per card of the mirrored apps (DB_APPS left out): frontmatter
                  fields only, the PR link, the time the card first became built (Done or
                  Released) per the vault's git history, and for unfinished cards the first line
                  of its running notes. The page loads it as one of its own files.
and prints each app's numbers as the vault's Dashboard note shows them: the summary tile
(_scripts/summary/view.js: current phase x/y) and the per-app block (_scripts/app-progress/view.js:
"Phase X" while the phase is before the license, else "Before the license" over stages 0 and 1).
DB apps are printed from their frozen vault snapshot, for comparison only.

Run it after every vault commit that touches a mirrored card, then publish mirror.js: the page
only knows the vault as of the last sync (a stale mirror is how AppD showed 99% on
2026-11-06 while Obsidian showed 100%).

Re-running rebuilds the file whole from the vault, so it is idempotent. Publishing it needs the
claude-artifacts tools (a Claude thread); the exact call is printed at the end:
  publish_files slug=<ARTIFACT_SLUG> base_version=<live version> mode=patch
                files=[{as: "mirror.js", path: "<OUT>/mirror.js"}]

Usage:
  python3 ~/.claude/lead/dashboard/sync_vault.py [--vault PATH]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path



def _roadmap() -> dict:
    """`roadmap` from ~/.claude/lead/config.json (the artifact and the vault are the owner's, not the repo's)."""
    try:
        return json.loads((Path.home() / ".claude" / "lead" / "config.json").read_text()).get("roadmap") or {}
    except (OSError, ValueError):
        return {}


_R = _roadmap()
ARTIFACT_SLUG = (_R.get("dashboard") or {}).get("artifact_slug") or "<artifact-slug>"
ARTIFACT_URL = (_R.get("dashboard") or {}).get("url") or "<dashboard-url>"
DEFAULT_VAULT = Path((_R.get("vault") or {}).get("path") or "~/Github/roadmap-vault").expanduser()
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
# Apps whose cards live in the artifact database, not the mirror (keep in step with logic.js DB_APPS).
DB_APPS = {
    "FieldApp": {"collection": "fld", "prefix": "FLD"},
    "StudyApp": {"collection": "stu", "prefix": "STU"},
    "AppC": {"collection": "apc", "prefix": "APC"},
}
PILOT_APPS = set(DB_APPS)

# GitHub repo for each app (from Apps/<App>.md and the local clones' remotes).
REPOS = {
    "AppF": "appf",
    "AppG": "appg",
    "FieldApp": "fieldapp",
    "AppD": "appd",
    "AppC": "appc",
    "AppE": "appe",
    "StudyApp": "studyapp",
}
BUILT = {"Done", "Released"}
FIELDS = ["id", "app", "title", "stage", "status", "priority", "size", "area", "type"]


def id_num(card_id: str) -> int:
    try:
        return int(str(card_id).split("-")[1])
    except (IndexError, ValueError):
        return 0


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------- frontmatter ----------

def parse_scalar(raw: str):
    """The scalar YAML forms the cards use: quoted or bare strings, true/false, ints, [lists]."""
    v = raw.strip()
    if v == "":
        return ""
    if v[0] == '"' and v.endswith('"') and len(v) >= 2:
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return v[1:-1]
    if v[0] == "'" and v.endswith("'") and len(v) >= 2:
        return v[1:-1].replace("''", "'")
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [parse_scalar(x) for x in re.findall(r'"[^"]*"|\'[^\']*\'|[^,]+', inner)] if inner else []
    if v in ("true", "True"):
        return True
    if v in ("false", "False"):
        return False
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def split_card(text: str) -> tuple[dict, str, str]:
    """(frontmatter dict, raw frontmatter text, body) of a card file; body is everything after
    the closing '---' line, verbatim."""
    m = re.match(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
    if not m:
        return {}, "", text
    raw = m.group(1)
    fm: dict = {}
    for line in raw.splitlines():
        lm = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", line)
        if lm:
            fm[lm.group(1)] = parse_scalar(lm.group(2))
    return fm, raw, text[m.end():]


def first_note(body: str, limit: int = 220) -> str:
    """First paragraph under the H1 (the card's running notes), as one trimmed line."""
    para: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("#"):
            if para:
                break
            continue
        if not s:
            if para:
                break
            continue
        para.append(s)
    note = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", " ".join(para))
    note = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", note)
    return note if len(note) <= limit else note[: limit - 1].rstrip() + "…"


def pr_link(app: str, pr) -> tuple[str, str]:
    """(label, url) for a card's pr field: a number, '#73', a full URL, 'repo#N' or 'repo #N'."""
    s = str(pr if pr is not None else "").strip()
    if not s:
        return "", ""
    m = re.search(r"https://github\.com/OWNER/([\w.-]+)/pull/(\d+)", s)
    if m:
        repo, n = m.group(1), m.group(2)
    else:
        m = re.search(r"([A-Za-z][\w.-]*)\s?#(\d+)", s)
        if m:
            repo, n = m.group(1), m.group(2)
        else:
            m = re.search(r"(\d+)", s)
            if not m:
                return s, ""
            repo, n = REPOS.get(app, ""), m.group(1)
    if not repo:
        return s, ""
    label = f"#{n}" if repo == REPOS.get(app) else f"{repo}#{n}"
    if re.search(r"\d+\D+\d+", re.sub(r"https://\S+/pull/", "", s)):
        label += " +"  # several PRs on one card; the link goes to the first
    return label, f"https://github.com/OWNER/{repo}/pull/{n}"


# ---------- git history ----------

def status_history(vault: Path) -> dict[str, list[dict]]:
    """Map card path -> every status the vault's git history gave it, oldest first:
    [{status, at (commit time, ISO), note (commit subject), added (bool: the commit added the file)}].
    Only commits where the status line changed (or the file was added) appear."""
    log = subprocess.run(
        ["git", "-C", str(vault), "log", "--reverse", "--no-renames", "-p", "-U0",
         "--format=@@COMMIT %cI%x09%s", "--", "Roadmaps"],
        capture_output=True, text=True, check=True,
    ).stdout
    hist: dict[str, list[dict]] = defaultdict(list)
    at = subject = path = None
    is_new = False
    for line in log.splitlines():
        if line.startswith("@@COMMIT "):
            at, _, subject = line[9:].partition("\t")
            continue
        if line.startswith("--- "):
            is_new = line == "--- /dev/null"
            continue
        if line.startswith("+++ "):
            path = line[6:].rstrip("\t") if line.startswith("+++ b/") else None  # tab ends a spaced path
            continue
        if path and line.startswith("+status:"):
            st = str(parse_scalar(line[len("+status:"):]))
            h = hist[path]
            if not h or h[-1]["status"] != st:
                h.append({"status": st, "at": at, "note": subject.strip(), "added": is_new})
    return hist


def first_built_at(h: list[dict], migrated: bool) -> str:
    """Commit time (ISO) the card first became built; '' when it arrived built from the Notion
    migration, whose real build day the vault doesn't know."""
    for i, e in enumerate(h):
        if e["status"] in BUILT:
            if i == 0 and e["added"] and migrated:
                return ""
            return e["at"]
    return ""


def git_head(vault: Path) -> tuple[str, str]:
    out = subprocess.run(["git", "-C", str(vault), "log", "-1", "--format=%h %cI"],
                         capture_output=True, text=True).stdout.split()
    return (out[0], out[1]) if len(out) == 2 else ("", "")


# ---------- reading the vault ----------

def read_cards(vault: Path, with_history: bool = True) -> list[dict]:
    """Every card as {fm, raw, body, rel, history}."""
    hist = status_history(vault) if with_history else {}
    cards = []
    for f in sorted((vault / "Roadmaps").glob("*/*.md")):
        text = f.read_text(encoding="utf-8")
        fm, raw, body = split_card(text)
        if not fm.get("id") or not fm.get("app"):
            continue
        rel = str(f.relative_to(vault))
        cards.append({"fm": fm, "raw": raw, "body": body, "rel": rel, "history": hist.get(rel, []),
                      "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()})
    return cards


def mirror_row(c: dict) -> dict:
    fm = c["fm"]
    status = str(fm.get("status") or "")
    built = status in BUILT
    pr_raw = str(fm.get("pr") if fm.get("pr") is not None else "").strip()
    pr_label, pr_url = pr_link(fm["app"], pr_raw)
    row = {k: str(fm.get(k) or "") for k in FIELDS}
    row.update({
        "needs_j": fm.get("needs_j") is True,  # Obsidian's dashboard counts only a YAML true
        "pr": pr_raw, "pr_label": pr_label, "pr_url": pr_url,
        "created": str(fm.get("created") or ""),
        "built_at": first_built_at(c["history"], bool(fm.get("notion"))) if built else "",
        "note": "" if built else first_note(c["body"]),
        # When the card last changed status per the vault's git history (the page's "In flight" age).
        "status_at": c["history"][-1]["at"] if c["history"] else "",
    })
    return row


# ---------- the summary, as _scripts/summary/view.js computes it ----------

def js_round(x: float) -> int:
    """Math.round, as Obsidian and the page round (Python's round() rounds 12.5 to 12)."""
    return int(math.floor(x + 0.5))


def summarize(rows: list[dict]) -> list[dict]:
    by_app = defaultdict(list)
    for r in rows:
        by_app[r["app"]].append(r)
    out = []
    for app in sorted(by_app, key=str.lower):
        cs = by_app[app]
        built = lambda c: c["status"] in BUILT  # noqa: E731
        stages = sorted({c["stage"] for c in cs if c["stage"]}, key=lambda s: (s == "After 1.0", s.lower()))
        phase = next((s for s in stages if any(c["stage"] == s and not built(c) for c in cs)), None)
        in_phase = [c for c in cs if c["stage"] == phase]
        done = sum(built(c) for c in in_phase)
        pre = [c for c in cs if re.match(r"^[01] ", c["stage"])]
        head = in_phase if phase and re.match(r"^[01] ", phase) else pre
        head_done = sum(built(c) for c in head)
        out.append({
            "app": app, "phase": phase or "All stages done", "built": done, "total": len(in_phase),
            "pct": js_round(done * 100 / len(in_phase)) if in_phase else 100,
            "head_label": f"Phase {phase}" if phase and re.match(r"^[01] ", phase) else "Before the license",
            "head_built": head_done, "head_total": len(head),
            "head_pct": js_round(head_done * 100 / len(head)) if head else 0,
            "license": sum(1 for c in cs if c["stage"] and not re.match(r"^[01] ", c["stage"])
                           and c["stage"] != "After 1.0" and not built(c)),
            "review": sum(c["status"] == "In review" for c in cs),
            "progress": sum(c["status"] == "In progress" for c in cs),
            "release": sum(c["status"] == "Done" and bool(c["pr"]) for c in cs),
            "needs_you": sum(c["needs_j"] is True and not built(c) for c in in_phase),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    args = ap.parse_args()

    cards = read_cards(args.vault)
    rows = [mirror_row(c) for c in cards]
    for c in cards:
        if not isinstance(c["fm"].get("needs_j"), bool):
            print(f"  note: {c['fm']['id']} needs_j is not a YAML boolean (counted as false, as Obsidian does)")
    mirror = sorted((r for r in rows if r["app"] not in PILOT_APPS), key=lambda r: (r["app"], r["id"]))
    head, head_at = git_head(args.vault)
    payload = {"synced_at": now_iso(), "vault_commit": head, "vault_commit_at": head_at,
               "apps": sorted({r["app"] for r in mirror}), "cards": mirror}
    OUT.mkdir(parents=True, exist_ok=True)
    js = "window.ROADMAP_MIRROR = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (OUT / "mirror.js").write_text(js, encoding="utf-8")

    print(f"{len(mirror)} mirrored cards (of {len(rows)}) from {args.vault} at {head} ({head_at})")
    print(f"wrote {OUT / 'mirror.js'} ({len(js.encode()) // 1024} KB)")
    for r in summarize(rows):
        tag = " [vault snapshot; live numbers are in the artifact]" if r["app"] in PILOT_APPS else ""
        print(f"  {r['app']}: app block \"{r['head_label']}: {r['head_pct']}%\" {r['head_built']}/{r['head_total']}; "
              f"summary tile Phase {r['phase']} {r['pct']}% {r['built']}/{r['total']}; "
              f"{r['license']} wait on the license, {r['review']} in review, {r['progress']} in progress, "
              f"{r['release']} need release, {r['needs_you']} need you this phase{tag}")
    print(f"""
Publish to {ARTIFACT_URL} (a Claude thread with the claude-artifacts tools):
  get_artifact slug={ARTIFACT_SLUG}   -> version
  publish_files slug={ARTIFACT_SLUG} base_version=<version> mode=patch label="vault sync {head}"
                files=[{{"as": "mirror.js", "path": "{OUT / 'mirror.js'}"}}]
  (If publish_files refuses the path because ~/.claude/lead isn't one of the session's folders,
   copy mirror.js into the session's scratchpad and publish that path.)""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
