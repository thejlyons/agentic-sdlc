#!/usr/bin/env python3
# Live version as of 2026-11-20, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
"""Build db_write payloads for the roadmap cards kept in the studio roadmap artifact's database.

Apps whose cards live in the database (see ROADMAP-DB.md), one collection each:
  FieldApp -> fld/FLD-<n>   (since 2026-11-05, vault snapshot 97a0f33)
  StudyApp     -> stu/STU-<n>   (since 2026-11-06)
  AppC  -> apc/APC-<n>     (since 2026-11-11, vault snapshot 1146862)
  AppD -> apd/APD-<n>  (since 2026-11-20, vault snapshot 372b06a)
Adding an app: put it in sync_vault.DB_APPS and logic.js DB_APPS, then `import --app <App>`.

The database can only be written through the claude-artifacts MCP tools (db_write) or from the
page itself; there is no shell or HTTP path. So this helper never writes anything remote: it
prints (or saves) the exact `ops` a Claude thread passes to db_write.

Commands
  import --app APP [--out DIR]
      One `set` op per card of APP in the vault (frontmatter, full body, status history from the
      vault's git log), split into batches under 58 KB and 50 ops: DIR/batch_01.json, ...
      (default out/<collection>_import). Each file is {"ops": [...]}: pass its ops to db_write as
      they are. Only for cards not in the database yet: `set` on an existing card needs ifVersion
      and would overwrite edits made since.

  seed --app APP [--out FILE]
      The same documents as one page file (window.<COLLECTION>_SEED), for an import the page runs
      itself on the owner's visit. FieldApp's first import was done this way (fld_seed.js).

  op CARD.json [--status S] [--pr N] [--needs-j true|false] [--note TEXT] [--comment TEXT] [--by WHO]
      CARD.json is the card as db_get returns it: {"version": n, "data": {...}}. Prints one
      db_write `update` op (collection from the card's app) with ifVersion, the changed fields,
      updated/updated_by, and the whole history array with the new entry appended (arrays
      replace wholesale in an update, so the full array is always sent).

  new --app APP --id ID --title T --stage S [--area A] [--type T] [--size S] [--priority P]
      [--needs-j true|false] [--body TEXT] [--note WHY] [--by WHO]
      Prints the `set` op for a new card (no ifVersion). ID: one more than the highest in
      `db_list collection=<collection>`.

  to-md CARD.json
      Prints the card back as a vault markdown file (frontmatter + body).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_vault as sv  # noqa: E402

DB_APPS = sv.DB_APPS  # app -> {"collection", "prefix"}
STATUSES = ["Backlog", "Next", "In progress", "In review", "Done", "Released"]
FM_ORDER = ["id", "app", "title", "stage", "area", "type", "size", "priority", "status", "needs_j",
            "pr", "created", "notion", "tags"]


def collection_of(app: str) -> str:
    if app not in DB_APPS:
        sys.exit(f"{app!r} isn't kept in the database (DB apps: {', '.join(DB_APPS)})")
    return DB_APPS[app]["collection"]


def card_doc(c: dict, head: str, at: str) -> dict:
    fm = c["fm"]
    needs_j = fm.get("needs_j")
    doc = {
        "id": fm["id"], "app": fm["app"], "title": str(fm.get("title") or ""),
        "stage": str(fm.get("stage") or ""), "area": str(fm.get("area") or ""),
        "type": str(fm.get("type") or ""), "size": str(fm.get("size") or ""),
        "priority": str(fm.get("priority") or ""), "status": str(fm.get("status") or ""),
        "needs_j": needs_j is True,
        "pr": str(fm.get("pr") if fm.get("pr") is not None else "").strip(),
        "created": str(fm.get("created") or ""),
        "tags": fm.get("tags") if isinstance(fm.get("tags"), list) else [],
        "body": c["body"],
        "comments": [],
        "history": [
            {"status": e["status"], "at": e["at"], "note": e["note"], "by": "vault",
             **({"imported": True} if i == 0 and e["added"] and fm.get("notion") else {})}
            for i, e in enumerate(c["history"])
        ],
        "updated": at, "updated_by": "import from vault",
        "source": {"file": c["rel"], "vault_commit": head, "frontmatter_raw": c["raw"],
                   "body_sha256": c["sha256"]},
    }
    if fm.get("notion"):
        doc["notion"] = str(fm["notion"])
    if not isinstance(needs_j, bool):
        doc["needs_j_text"] = str(needs_j)
    extra = {k: v for k, v in fm.items() if k not in FM_ORDER}
    if extra:
        doc["extra"] = extra
    return doc


def app_cards(vault: Path, app: str) -> list[dict]:
    cards = [c for c in sv.read_cards(vault) if c["fm"]["app"] == app]
    cards.sort(key=lambda c: sv.id_num(c["fm"]["id"]))
    return cards


def cmd_import(args) -> int:
    col = collection_of(args.app)
    cards = app_cards(args.vault, args.app)
    head, _ = sv.git_head(args.vault)
    at = sv.now_iso()
    out = Path(args.out or sv.OUT / f"{col}_import")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("batch_*.json"):
        old.unlink()
    batches, cur, size = [], [], 0
    for c in cards:
        op = {"op": "set", "path": f"{col}/{c['fm']['id']}", "data": card_doc(c, head, at)}
        n = len(json.dumps(op, ensure_ascii=False).encode())
        if cur and (size + n > 58_000 or len(cur) == 50):
            batches.append(cur)
            cur, size = [], 0
        cur.append(op)
        size += n
    if cur:
        batches.append(cur)
    for i, b in enumerate(batches, 1):
        p = out / f"batch_{i:02d}.json"
        p.write_text(json.dumps({"ops": b}, ensure_ascii=False), encoding="utf-8")
        print(f"{p}  {len(b)} cards  {p.stat().st_size // 1024} KB  {b[0]['path']}..{b[-1]['path']}")
    print(f"{len(cards)} {args.app} cards from vault commit {head}")
    return 0


def cmd_seed(args) -> int:
    col = collection_of(args.app)
    cards = app_cards(args.vault, args.app)
    head, head_at = sv.git_head(args.vault)
    at = sv.now_iso()
    seed = {"vault_commit": head, "vault_commit_at": head_at, "made_at": at,
            "cards": [card_doc(c, head, at) for c in cards]}
    out = Path(args.out or sv.OUT / f"{col}_seed.js")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"window.{col.upper()}_SEED = " + json.dumps(seed, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB, {len(cards)} cards, vault {head})")
    return 0


def load_card(path: str) -> tuple[int, dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8") if path != "-" else sys.stdin.read())
    if "data" in raw:
        return int(raw.get("version") or 0), raw["data"]
    return int(raw.get("version") or 0), raw


def cmd_op(args) -> int:
    version, card = load_card(args.card)
    if not version:
        sys.exit("CARD.json needs the document's version (from db_get)")
    col = collection_of(card.get("app", ""))
    at = sv.now_iso()
    data: dict = {"updated": at, "updated_by": args.by}
    if args.status:
        if args.status not in STATUSES:
            sys.exit(f"status must be one of {STATUSES}")
        data["status"] = args.status
    if args.pr is not None:
        data["pr"] = str(args.pr)
    if args.needs_j is not None:
        data["needs_j"] = args.needs_j == "true"
    if args.status or args.note:
        entry = {"status": args.status or card.get("status", ""), "at": at, "by": args.by}
        if args.note:
            entry["note"] = args.note
        data["history"] = list(card.get("history") or []) + [entry]
    if args.comment:
        data["comments"] = list(card.get("comments") or []) + [{"at": at, "by": args.by, "text": args.comment}]
    print(json.dumps({"op": "update", "path": f"{col}/{card['id']}", "ifVersion": version,
                      "data": data}, ensure_ascii=False, indent=2))
    return 0


def cmd_new(args) -> int:
    col = collection_of(args.app)
    prefix = DB_APPS[args.app]["prefix"]
    if not args.id.startswith(prefix + "-"):
        sys.exit(f"{args.app} ids start with {prefix}-")
    at = sv.now_iso()
    body = args.body if args.body is not None else f"\n# {args.title}\n\n\n\n## Done when\n- [ ] \n"
    doc = {
        "id": args.id, "app": args.app, "title": args.title, "stage": args.stage, "area": args.area or "",
        "type": args.type or "", "size": args.size or "", "priority": args.priority or "",
        "status": "Backlog", "needs_j": args.needs_j == "true", "pr": "",
        "created": dt.date.today().isoformat(), "tags": ["card"], "body": body, "comments": [],
        "history": [{"status": "Backlog", "at": at, "by": args.by, "note": "filed: " + (args.note or "")}],
        "updated": at, "updated_by": args.by, "source": {},
    }
    print(json.dumps({"op": "set", "path": f"{col}/{args.id}", "data": doc}, ensure_ascii=False, indent=2))
    return 0


def yaml_str(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return "[" + ", ".join(json.dumps(x, ensure_ascii=False) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)


def cmd_to_md(args) -> int:
    _, card = load_card(args.card)
    sys.stdout.write(card_to_md(card))
    return 0


def card_to_md(card: dict) -> str:
    """The card as a vault file. While its frontmatter fields still equal the imported ones, the
    imported frontmatter text is reused byte for byte; otherwise it is written fresh."""
    raw = (card.get("source") or {}).get("frontmatter_raw")
    if raw:
        fm, _, _ = sv.split_card("---\n" + raw + "\n---\n")
        same = all(
            (card.get(k) == (fm.get(k) is True) if k == "needs_j" and "needs_j_text" not in card
             else str(card.get(k, "")) == str(fm.get(k) if fm.get(k) is not None else "")
             if k != "tags" else card.get(k) == fm.get(k))
            for k in FM_ORDER if k in card or k in fm)
        if same:
            return "---\n" + raw + "\n---\n" + card.get("body", "")
    lines = ["---"]
    for k in FM_ORDER:
        if k in card and (k != "notion" or card.get(k)):
            lines.append(f"{k}: {yaml_str(card[k])}")
    for k, v in (card.get("extra") or {}).items():
        lines.append(f"{k}: {yaml_str(v)}")
    lines.append("---")
    return "\n".join(lines) + "\n" + card.get("body", "")


def main(argv=None, default_app: str | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("import", cmd_import), ("seed", cmd_seed)):
        p = sub.add_parser(name)
        p.add_argument("--app", required=default_app is None, default=default_app, choices=list(DB_APPS))
        p.add_argument("--vault", type=Path, default=sv.DEFAULT_VAULT)
        p.add_argument("--out")
        p.set_defaults(fn=fn)
    p = sub.add_parser("op")
    p.add_argument("card")
    p.add_argument("--status")
    p.add_argument("--pr")
    p.add_argument("--needs-j", choices=["true", "false"])
    p.add_argument("--note")
    p.add_argument("--comment")
    p.add_argument("--by", default="claude")
    p.set_defaults(fn=cmd_op)
    p = sub.add_parser("new")
    p.add_argument("--app", required=default_app is None, default=default_app, choices=list(DB_APPS))
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--stage", required=True)
    for k in ("area", "type", "size", "priority", "body", "note"):
        p.add_argument("--" + k)
    p.add_argument("--needs-j", choices=["true", "false"], default="false")
    p.add_argument("--by", default="claude")
    p.set_defaults(fn=cmd_new)
    p = sub.add_parser("to-md")
    p.add_argument("card")
    p.set_defaults(fn=cmd_to_md)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
