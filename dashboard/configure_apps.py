#!/usr/bin/env python3
"""Make a copy of the dashboard page and tools for the real apps in the private config.

The files in this folder name the example apps (FieldApp, StudyApp, ...) in a few constants. This
script copies them to an output folder OUTSIDE the repo and rewrites those constants from
~/.claude/lead/config.json (`apps`, `owner.github`):

  site/logic.js    APPS, DB_APPS, REPOS, the GitHub owner in the PR links
  site/app.js      COLOR_ORDER (which tile colour each app gets)
  sync_vault.py    DB_APPS, REPOS, the GitHub owner in the PR links
  site/index.html, roadmap_card.py, ROADMAP-DB.md   copied as they are

An app with `"roadmap": "dashboard"` becomes a database app (its `collection` and `prefix`); any
other app is shown read-only from mirror.js. The tests are not copied: tests/logic.test.js pins the
example names, so run the tests in the repo, not in the copy.

It stops with an error, writing nothing, if a constant is not found exactly once: the live file
changed and this script must be updated first.

  python3 dashboard/configure_apps.py --dry-run
  python3 dashboard/configure_apps.py [--config PATH] [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
COPY = ["site/index.html", "site/app.js", "site/logic.js", "roadmap_card.py", "sync_vault.py", "ROADMAP-DB.md"]
NAME_OK = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]*")
OWNER_OK = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")
MAX_COLOURS = 7  # index.html defines --s1 to --s7


class ConfigError(Exception):
    pass


def read_apps(cfg: dict) -> tuple[list[dict], str]:
    owner = str((cfg.get("owner") or {}).get("github") or "")
    if not OWNER_OK.fullmatch(owner):
        raise ConfigError(f"owner.github is not a GitHub account name: {owner!r}")
    apps, seen = [], set()
    for a in cfg.get("apps") or []:
        name, prefix = str(a.get("name") or ""), str(a.get("prefix") or "")
        if not NAME_OK.fullmatch(name) or not re.fullmatch(r"[A-Z][A-Z0-9]*", prefix):
            raise ConfigError(f"app needs a plain name and an upper-case prefix: {a!r}")
        if name in seen or prefix in seen:
            raise ConfigError(f"app name or prefix used twice: {name} / {prefix}")
        seen.update((name, prefix))
        in_db = a.get("roadmap") == "dashboard"
        col = str(a.get("collection") or "")
        if in_db and (not re.fullmatch(r"[a-z][a-z0-9_]*", col) or col == "meta"):
            raise ConfigError(f"{name}: a database app needs a lower-case collection name other than meta, got {col!r}")
        repo = str(a.get("repo") or "").split("/")[-1]
        if repo and not re.fullmatch(r"[\w.-]+", repo):
            raise ConfigError(f"{name}: repo is not a repository name: {a.get('repo')!r}")
        apps.append({"name": name, "prefix": prefix, "collection": col, "db": in_db, "repo": repo})
    if not apps:
        raise ConfigError("the config lists no apps")
    return apps, owner


def sub_once(text: str, pattern: str, new: str, what: str, flags: int = 0, count: int = 1) -> str:
    found = len(re.findall(pattern, text, flags))
    if found != count:
        raise ConfigError(f"expected {count} of {what}, found {found}: the file changed, update configure_apps.py")
    return re.sub(pattern, lambda _m: new, text, flags=flags)


def js(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def configure_logic(text: str, apps: list[dict], owner: str) -> str:
    db = "".join(f"\n    {js(a['name'])}: {{ collection: {js(a['collection'])}, prefix: {js(a['prefix'])} }}," for a in apps if a["db"])
    repos = "".join(f"\n    {js(a['name'])}: {js(a['repo'])}," for a in apps if a["repo"])
    text = sub_once(text, r"const APPS = \[[^\]]*\];", f"const APPS = {js([a['name'] for a in apps])};", "logic.js APPS")
    text = sub_once(text, r"const DB_APPS = \{.*?\n  \};", "const DB_APPS = {" + db + "\n  };", "logic.js DB_APPS", re.S)
    text = sub_once(text, r"const REPOS = \{.*?\n  \};", "const REPOS = {" + repos + "\n  };", "logic.js REPOS", re.S)
    text = sub_once(text, r"github\\\.com\\/OWNER\\/", f"github\\.com\\/{owner}\\/", "logic.js PR link pattern")
    return sub_once(text, r"github\.com/OWNER/", f"github.com/{owner}/", "logic.js PR link")


def configure_app_js(text: str, apps: list[dict]) -> str:
    return sub_once(text, r"const COLOR_ORDER = \[[^\]]*\];", f"const COLOR_ORDER = {js([a['name'] for a in apps])};",
                    "app.js COLOR_ORDER")


def configure_sync_vault(text: str, apps: list[dict], owner: str) -> str:
    db = "".join(f"    {js(a['name'])}: {{\"collection\": {js(a['collection'])}, \"prefix\": {js(a['prefix'])}}},\n"
                 for a in apps if a["db"])
    repos = "".join(f"    {js(a['name'])}: {js(a['repo'])},\n" for a in apps if a["repo"])
    text = sub_once(text, r"^DB_APPS = \{\n.*?^\}\n", "DB_APPS = {\n" + db + "}\n", "sync_vault.py DB_APPS", re.S | re.M)
    text = sub_once(text, r"^REPOS = \{\n.*?^\}\n", "REPOS = {\n" + repos + "}\n", "sync_vault.py REPOS", re.S | re.M)
    text = sub_once(text, r"github\\\.com/OWNER/", f"github\\.com/{owner}/", "sync_vault.py PR link pattern")
    return sub_once(text, r"github\.com/OWNER/", f"github.com/{owner}/", "sync_vault.py PR link")


def build(src: Path, apps: list[dict], owner: str) -> dict[str, str]:
    out = {rel: (src / rel).read_text(encoding="utf-8") for rel in COPY}
    out["site/logic.js"] = configure_logic(out["site/logic.js"], apps, owner)
    out["site/app.js"] = configure_app_js(out["site/app.js"], apps)
    out["sync_vault.py"] = configure_sync_vault(out["sync_vault.py"], apps, owner)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=Path("~/.claude/lead/config.json").expanduser())
    ap.add_argument("--src", type=Path, default=HERE, help="the dashboard folder to copy from")
    ap.add_argument("--out", type=Path, default=Path("~/.claude/lead/dashboard/build").expanduser())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    out_dir = args.out.expanduser().resolve()
    try:
        if out_dir == REPO or REPO in out_dir.parents:
            raise ConfigError(f"--out must be outside the repo ({REPO}): the configured copy names the real apps")
        cfg = json.loads(args.config.expanduser().read_text(encoding="utf-8"))
        apps, owner = read_apps(cfg)
        files = build(args.src, apps, owner)
    except (ConfigError, OSError, ValueError) as e:
        print(f"configure_apps: {e}", file=sys.stderr)
        return 1
    db_apps = [a for a in apps if a["db"]]
    print(f"{len(apps)} apps, {len(db_apps)} in the database, GitHub owner {owner}")
    for a in apps:
        where = f"database collection {a['collection']}" if a["db"] else "mirror.js (markdown vault)"
        print(f"  {a['name']} ({a['prefix']}-n): {where}; repo {a['repo'] or 'none'}")
    if len(apps) > MAX_COLOURS:
        print(f"  note: index.html defines {MAX_COLOURS} tile colours; add --s{MAX_COLOURS + 1} and up for the rest")
    for rel in COPY:
        src_text = (args.src / rel).read_text(encoding="utf-8")
        changed = sum(1 for a, b in zip(src_text.split("\n"), files[rel].split("\n")) if a != b) + \
            abs(len(src_text.split("\n")) - len(files[rel].split("\n")))
        print(f"  {'would write' if args.dry_run else 'wrote'} {out_dir / rel} ({'rewritten' if changed else 'copied as is'})")
    if args.dry_run:
        return 0
    for rel, text in files.items():
        p = out_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        shutil.copymode(args.src / rel, p)
    print("Next: put mirror.js and one <collection>_seed.js per database app beside index.html (RESTORE.md, step 2).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
