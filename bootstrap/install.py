#!/usr/bin/env python3
"""Install, check or remove the lead loop on this machine (python3 standard library only).

  python3 bootstrap/install.py --dry-run             print every action, write nothing
  python3 bootstrap/install.py [--yes]               install or update; a second run reports "unchanged"
  python3 bootstrap/install.py --config FILE [--yes] also validate FILE and install it as the private config
  python3 bootstrap/install.py --validate FILE       only validate a config file
  python3 bootstrap/install.py --check               exit 1 if anything installed differs from this repo
  python3 bootstrap/install.py --uninstall [--purge] remove what was installed (--purge: also the private
                                                     config and the working folders)

What goes where (all under the home folder; HOME is honoured, so HOME=$(mktemp -d) gives a test install):
  skills/<name>/SKILL.md  -> ~/.claude/skills/<name>/SKILL.md
  agents/*.md             -> ~/.claude/agents/
  hooks/guard.py, attention.py -> ~/.claude/hooks/
  scripts/macgate.sh macstop.sh waitgate.sh waitci.sh -> ~/.claude/lead/bin/
  dashboard/ (not out/)   -> ~/.claude/lead/dashboard/
  rules/                  -> ~/.claude/lead/rules/
  working folders         ~/.claude/lead/{briefs,handbacks,research}, queue.md, attention.jsonl
  private config          ~/.claude/lead/config.json (from --config; never from the repo by itself)
  derived                 ~/.claude/lead/machine.env (from config.json; the scripts source it)
  settings                the hooks and allow rules of hooks/settings.example.json merged into
                          ~/.claude/settings.json: only missing entries are added, the diff is shown, the
                          old file is backed up, and nothing is written without --yes or a "y" at the prompt
  manifest                ~/.claude/lead/.install-manifest.json (what was installed, with checksums)

Rules it keeps:
  - A destination file that differs and that this installer did not put there is the owner's: it is kept
    and listed, unless --force (which backs it up first).
  - --uninstall removes only files that still match what was installed; changed files are left and listed.
  - config.json, briefs, hand-backs, the queue and the attention log are never deleted without --purge.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOME = Path.home()
CLAUDE = HOME / ".claude"
LEAD = CLAUDE / "lead"
SETTINGS = CLAUDE / "settings.json"
MANIFEST = LEAD / ".install-manifest.json"
CONFIG = LEAD / "config.json"
ENV = LEAD / "machine.env"
SCRIPTS = ["macgate.sh", "macstop.sh", "waitgate.sh", "waitci.sh"]
HOOKS = ["guard.py", "attention.py"]
WORK_DIRS = ["briefs", "handbacks", "research"]
WORK_FILES = ["queue.md", "attention.jsonl"]
SKIP_DIRS = {"__pycache__", "out", ".git"}
HOOK_MARKS = [".claude/hooks/guard.py", ".claude/hooks/attention.py"]
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
NOW = dt.datetime.now().strftime("%Y%m%d-%H%M%S")


class Run:
    def __init__(self, dry: bool):
        self.dry = dry
        self.counts: dict[str, int] = {}
        self.problems: list[str] = []

    def say(self, verb: str, what: str, note: str = "") -> None:
        self.counts[verb] = self.counts.get(verb, 0) + 1
        if verb != "unchanged":
            print(f"{'would ' if self.dry and verb not in ('kept', 'left', 'missing', 'differs') else ''}{verb:<10} {what}"
                  + (f"  ({note})" if note else ""))

    def summary(self) -> str:
        return ", ".join(f"{n} {v}" for v, n in sorted(self.counts.items())) or "nothing to do"


def short(p: Path) -> str:
    try:
        return "~/" + p.relative_to(HOME).as_posix()
    except ValueError:
        return str(p)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tree(src: Path, dest: Path) -> list[tuple[Path, Path]]:
    if not src.is_dir():
        return []
    return [(p, dest / p.relative_to(src)) for p in sorted(src.rglob("*"))
            if p.is_file() and not (set(p.relative_to(src).parts) & SKIP_DIRS) and p.suffix != ".pyc"
            and p.name != ".DS_Store"]


def plan() -> list[tuple[Path, Path]]:
    """Every (repo file, destination) pair. Install is a plain copy: the files already name these places."""
    out: list[tuple[Path, Path]] = []
    for skill in sorted((REPO / "skills").glob("*/SKILL.md")):
        out.append((skill, CLAUDE / "skills" / skill.parent.name / "SKILL.md"))
    out += [(p, CLAUDE / "agents" / p.name) for p in sorted((REPO / "agents").glob("*.md"))]
    out += [(REPO / "hooks" / n, CLAUDE / "hooks" / n) for n in HOOKS]
    out += [(REPO / "scripts" / n, LEAD / "bin" / n) for n in SCRIPTS]
    out += tree(REPO / "dashboard", LEAD / "dashboard")
    out += tree(REPO / "rules", LEAD / "rules")
    return out


def load_manifest() -> dict:
    try:
        return json.loads(MANIFEST.read_text())
    except (OSError, ValueError):
        return {"files": {}, "settings": {}, "created": []}


def repo_commit() -> str:
    try:
        r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        return r.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


# ---------- config ----------

def validate(cfg: dict) -> list[str]:
    """Problems that would break the scripts, the guard or the skills. An empty list means usable."""
    bad: list[str] = []

    def need(path: str, kind):
        cur = cfg
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                bad.append(f"{path}: missing")
                return None
            cur = cur[part]
        if kind is not None and (not isinstance(cur, kind) or isinstance(cur, bool) and kind is not bool):
            bad.append(f"{path}: must be {getattr(kind, '__name__', 'a number')}")
            return None
        return cur

    num = (int, float)
    need("owner.name", str)
    need("lead.workspace", str)
    for key in ("machine.gate.max_load", "machine.gate.max_swap_mb", "machine.stop.swap_mb", "machine.stop.load",
                "machine.stop.min_free_pct", "machine.stop.grace_s"):
        need(key, num)
    need("guardrails.vault_repo", str)
    prot = need("guardrails.protected_paths", list)
    if prot is not None and not all(isinstance(p, str) and p.strip() for p in prot):
        bad.append("guardrails.protected_paths: every entry must be a path")
    need("guardrails.always_ask", list)
    for key in ("lead", "implementer", "reviewer", "reviewer_when_implementer_is_fable"):
        need("models." + key, str)
    apps = need("apps", list)
    seen_prefix, seen_prio = set(), set()
    for i, app in enumerate(apps or []):
        at = f"apps[{i}]"
        if not isinstance(app, dict):
            bad.append(f"{at}: must be an object")
            continue
        for key in ("name", "prefix", "repo", "path", "roadmap"):
            if not isinstance(app.get(key), str) or not app.get(key):
                bad.append(f"{at}.{key}: missing")
        if isinstance(app.get("repo"), str) and not REPO_RE.match(app["repo"]):
            bad.append(f"{at}.repo: must look like owner/name")
        if isinstance(app.get("prefix"), str) and not re.match(r"^[A-Z][A-Z0-9]{1,5}$", app["prefix"]):
            bad.append(f"{at}.prefix: 2 to 6 capital letters or digits")
        if app.get("roadmap") not in ("dashboard", "vault"):
            bad.append(f'{at}.roadmap: "dashboard" or "vault"')
        if app.get("roadmap") == "dashboard" and not re.match(r"^[a-z][a-z0-9]*$", str(app.get("collection") or "")):
            bad.append(f"{at}.collection: needed for a dashboard app (lower-case letters and digits)")
        if app.get("prefix") in seen_prefix:
            bad.append(f"{at}.prefix: used twice")
        seen_prefix.add(app.get("prefix"))
        prio = app.get("lane_priority")
        if prio is not None:
            if not isinstance(prio, int) or isinstance(prio, bool):
                bad.append(f"{at}.lane_priority: a whole number")
            elif prio in seen_prio:
                bad.append(f"{at}.lane_priority: {prio} used twice")
            seen_prio.add(prio)
    if apps is not None and not apps:
        bad.append("apps: at least one app")
    return bad


def placeholders(cfg: dict) -> list[str]:
    """Example values still in a config (a warning, not an error: the example config must install in tests)."""
    text = json.dumps(cfg)
    return [w for w in ("OWNER/", "FieldApp", "StudyApp", "~/Protected") if w in text]


def machine_env(cfg: dict) -> str:
    m, apps = cfg["machine"], cfg["apps"]
    on_machine = [a["repo"] for a in apps if (a.get("ci") or {}).get("runs_on_build_machine", True)]
    lane = sorted((a for a in apps if isinstance(a.get("lane_priority"), int)), key=lambda a: a["lane_priority"])
    first = (lane or apps)[0]["repo"]
    n = lambda v: str(int(v)) if float(v) == int(v) else str(float(v))  # noqa: E731
    lines = [
        "# Written by bootstrap/install.py from config.json (machine, apps). Do not edit: change config.json and",
        "# run install.py again. macgate.sh, macstop.sh and waitci.sh source this file.",
        f"GATE_MAX_LOAD={n(m['gate']['max_load'])}",
        f"GATE_MAX_SWAP_MB={n(m['gate']['max_swap_mb'])}",
        f'GATE_REPOS="{" ".join(on_machine)}"',
        f"STOP_SWAP_MB={n(m['stop']['swap_mb'])}",
        f"STOP_LOAD={n(m['stop']['load'])}",
        f"STOP_MIN_FREE_PCT={n(m['stop']['min_free_pct'])}",
        f"STOP_GRACE_S={n(m['stop']['grace_s'])}",
        f'CI_REPO="{first}"',
    ]
    if isinstance(m.get("disk_floor_gb"), (int, float)):
        lines.append(f"DISK_FLOOR_GB={n(m['disk_floor_gb'])}")
    return "\n".join(lines) + "\n"


def read_config(path: Path) -> dict:
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"{path}: cannot read as JSON ({e})")
    problems = validate(cfg) if isinstance(cfg, dict) else ["the file must hold one JSON object"]
    if problems:
        sys.exit(f"{path} is not a usable config:\n  " + "\n  ".join(problems) + "\nSee config/SCHEMA.md.")
    return cfg


def write_text(run: Run, dest: Path, text: str, label: str, manifest: dict, track: bool) -> None:
    old = dest.read_text(encoding="utf-8") if dest.exists() else None
    if old == text:
        run.say("unchanged", short(dest))
    else:
        if old is not None and not track:
            lines = list(difflib.unified_diff(old.splitlines(), text.splitlines(), "current", "new", lineterm="", n=1))
            print(f"--- {short(dest)} changes ({label}):")
            print("\n".join(lines[:60]) + ("\n… (diff cut)" if len(lines) > 60 else ""))
        run.say("write" if old is None else "update", short(dest), label)
        if not run.dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if old is not None and not track:
                shutil.copy2(dest, dest.with_name(dest.name + f".bak-{NOW}"))
            dest.write_text(text, encoding="utf-8")
    if track and not run.dry:
        manifest["files"][short(dest)] = hashlib.sha256(text.encode()).hexdigest()


# ---------- settings ----------

def wanted_settings() -> dict:
    ex = json.loads((REPO / "hooks" / "settings.example.json").read_text(encoding="utf-8"))
    fix = lambda rule: rule.replace("~/", HOME.as_posix() + "/")  # noqa: E731
    return {"allow": [fix(r) for r in ex["permissions"].get("allow", [])],
            "ask": [fix(r) for r in ex["permissions"].get("ask", [])],
            "hooks": ex["hooks"]}


def has_hook(groups: list, mark: str) -> bool:
    return any(mark in str(h.get("command", "")) for g in groups or [] if isinstance(g, dict)
               for h in g.get("hooks") or [] if isinstance(h, dict))


def merged_settings(cur: dict, manifest: dict) -> tuple[dict, dict]:
    """(settings with the missing entries added, what was added). Existing entries are never changed."""
    want = wanted_settings()
    new = json.loads(json.dumps(cur))
    added = {"allow": [], "ask": [], "hooks": []}
    perms = new.setdefault("permissions", {})
    for key in ("allow", "ask"):
        have = perms.setdefault(key, [])
        for rule in want[key]:
            if rule not in have:
                have.append(rule)
                added[key].append(rule)
    hooks = new.setdefault("hooks", {})
    for event, groups in want["hooks"].items():
        for group in groups:
            mark = next(m for m in HOOK_MARKS if m in group["hooks"][0]["command"])
            if not has_hook(hooks.get(event), mark):
                hooks.setdefault(event, []).append(group)
                added["hooks"].append(mark)
    for key in ("allow", "ask"):
        if not perms[key] and key not in (cur.get("permissions") or {}):
            del perms[key]
    return new, added


def stripped_settings(cur: dict, manifest: dict) -> dict:
    """Settings without what this installer added: its hook entries, and the rules the manifest recorded."""
    new = json.loads(json.dumps(cur))
    rec = manifest.get("settings") or {}
    perms = new.get("permissions") or {}
    for key in ("allow", "ask"):
        if key in perms:
            perms[key] = [r for r in perms[key] if r not in (rec.get(key) or [])]
    for key in ("allow", "ask"):
        if key in perms and not perms[key] and rec.get(key):
            del perms[key]
    if "permissions" in new and not new["permissions"]:
        del new["permissions"]
    hooks = new.get("hooks") or {}
    for event in list(hooks):
        groups = []
        for g in hooks[event]:
            if isinstance(g, dict):
                left = [h for h in g.get("hooks") or [] if not any(m in str(h.get("command", "")) for m in HOOK_MARKS)]
                if left or not g.get("hooks"):
                    groups.append({**g, "hooks": left} if g.get("hooks") else g)
            else:
                groups.append(g)
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]
    if "hooks" in new and not new["hooks"]:
        del new["hooks"]
    return new


def read_settings() -> dict:
    if not SETTINGS.exists():
        return {}
    try:
        cur = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.exit(f"{short(SETTINGS)} is not valid JSON ({e}). Fix it by hand first; nothing was changed.")
    if not isinstance(cur, dict):
        sys.exit(f"{short(SETTINGS)} must hold one JSON object. Nothing was changed.")
    return cur


def write_settings(run: Run, cur: dict, new: dict, yes: bool, why: str) -> bool:
    """Show the diff, ask, back up, write. Returns True when the file now holds `new`."""
    if new == cur:
        run.say("unchanged", short(SETTINGS))
        return True
    a = json.dumps(cur, indent=2).splitlines()
    b = json.dumps(new, indent=2).splitlines()
    print(f"--- {short(SETTINGS)}: {why}")
    print("\n".join(difflib.unified_diff(a, b, "settings.json (now)", "settings.json (after)", lineterm="", n=2)))
    if run.dry:
        run.say("merge", short(SETTINGS), "diff above")
        return False
    if not yes:
        if not sys.stdin.isatty():
            run.say("kept", short(SETTINGS), "not written: no terminal to ask; show the owner the diff, then run again with --yes")
            run.problems.append("settings.json was not changed (needs --yes)")
            return False
        if input("Write this change to settings.json? [y/N] ").strip().lower() not in ("y", "yes"):
            run.say("kept", short(SETTINGS), "you said no")
            run.problems.append("settings.json was not changed (declined)")
            return False
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS.exists():
        backup = SETTINGS.with_name(f"settings.json.bak-{NOW}")
        shutil.copy2(SETTINGS, backup)
        print(f"backup     {short(backup)}")
    SETTINGS.write_text(json.dumps(new, indent=2) + "\n", encoding="utf-8")
    run.say("merge", short(SETTINGS), "written")
    return True


# ---------- commands ----------

def install(args) -> int:
    run = Run(args.dry_run)
    manifest = load_manifest()
    cfg = read_config(Path(args.config).expanduser()) if args.config else None
    print(f"{'DRY RUN: nothing is written. ' if run.dry else ''}Installing from {REPO.name} at {repo_commit()} into {short(CLAUDE)}")

    for src, dest in plan():
        if not src.exists():
            run.say("missing", src.relative_to(REPO).as_posix(), "not in this repo checkout")
            run.problems.append(f"repo file missing: {src.relative_to(REPO)}")
            continue
        key, want = short(dest), sha(src)
        if not dest.exists():
            run.say("install", key)
        elif sha(dest) == want:
            run.say("unchanged", key)
            if not run.dry:
                manifest["files"][key] = want
            continue
        elif manifest["files"].get(key) == sha(dest):
            run.say("update", key, "the repo has a newer version")
        elif args.force:
            run.say("replace", key, f"your version is kept as {dest.name}.bak-{NOW}")
            if not run.dry:
                shutil.copy2(dest, dest.with_name(dest.name + f".bak-{NOW}"))
        else:
            n = sum(1 for l in difflib.unified_diff(dest.read_text(errors="replace").splitlines(),
                                                    src.read_text(errors="replace").splitlines(), lineterm="", n=0)
                    if l[:1] in "+-" and l[:3] not in ("+++", "---"))
            run.say("kept", key, f"differs from the repo in {n} lines and was not installed by this script; --force replaces it")
            run.problems.append(f"kept your own {key}")
            continue
        if not run.dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            dest.chmod(0o755 if dest.suffix in (".sh", ".py") else 0o644)
            manifest["files"][key] = want

    for name in WORK_DIRS:
        d = LEAD / name
        if d.is_dir():
            run.say("unchanged", short(d))
        else:
            run.say("create", short(d) + "/")
            if not run.dry:
                d.mkdir(parents=True, exist_ok=True)
                manifest.setdefault("created", []).append(short(d))
    for name in WORK_FILES:
        f = LEAD / name
        if f.exists():
            run.say("unchanged", short(f))
        else:
            run.say("create", short(f), "empty")
            if not run.dry:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.touch()
                manifest.setdefault("created", []).append(short(f))

    if cfg is not None:
        write_text(run, CONFIG, json.dumps(cfg, indent=2) + "\n", "private config", manifest, track=False)
        left = placeholders(cfg)
        if left:
            print(f"note       the config still holds example values ({', '.join(left)}): fine for a test, not for real work")
    elif CONFIG.exists():
        cfg = read_config(CONFIG)
        run.say("unchanged", short(CONFIG))
    if cfg is not None:
        write_text(run, ENV, machine_env(cfg), "from config.json", manifest, track=True)
    else:
        print(f"pending    {short(CONFIG)}: no private config yet. The scripts and the guard run on the example "
              "defaults until the interview is done (skill `bootstrap`, or --config FILE).")

    cur = read_settings()
    new, added = merged_settings(cur, manifest)
    if write_settings(run, cur, new, args.yes, "add the guard and attention hooks and the read-only allow rules"):
        rec = manifest.setdefault("settings", {})
        for key in ("allow", "ask", "hooks"):
            rec[key] = sorted(set(rec.get(key) or []) | set(added[key]))

    if not run.dry:
        manifest["repo_commit"] = repo_commit()
        manifest["installed_at"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"{'dry run' if run.dry else 'install'}: {run.summary()}")
    for p in run.problems:
        print("attention:", p)
    return 1 if any(p.startswith("repo file missing") for p in run.problems) else 0


def check(args) -> int:
    run = Run(False)
    for src, dest in plan():
        if not dest.exists():
            run.say("missing", short(dest))
        elif sha(dest) != sha(src):
            run.say("differs", short(dest))
        else:
            run.say("unchanged", short(dest))
    for name in WORK_DIRS + WORK_FILES:
        if not (LEAD / name).exists():
            run.say("missing", short(LEAD / name))
    cur = read_settings()
    for mark in HOOK_MARKS:
        event = "PreToolUse" if "guard" in mark else "Notification"
        if not has_hook((cur.get("hooks") or {}).get(event), mark):
            run.say("missing", f"{short(SETTINGS)}: {event} hook for {mark.rsplit('/', 1)[1]}")
    if CONFIG.exists():
        cfg = read_config(CONFIG)
        if not ENV.exists() or ENV.read_text() != machine_env(cfg):
            run.say("differs", short(ENV), "not what config.json gives; run install.py")
    else:
        print(f"pending    {short(CONFIG)}: no private config (the interview has not been done)")
    bad = run.counts.get("missing", 0) + run.counts.get("differs", 0)
    print(f"check: {run.summary()}")
    return 1 if bad else 0


def uninstall(args) -> int:
    run = Run(args.dry_run)
    manifest = load_manifest()
    if not MANIFEST.exists():
        print(f"No manifest at {short(MANIFEST)}: this script installed nothing here (or it was already removed).")
    for key, want in sorted(manifest.get("files", {}).items()):
        p = HOME / key[2:]
        if not p.exists():
            continue
        if sha(p) != want:
            run.say("left", key, "changed since it was installed")
            continue
        run.say("remove", key)
        if not run.dry:
            p.unlink()
    cur = read_settings()
    if cur:
        if write_settings(run, cur, stripped_settings(cur, manifest), args.yes, "remove the hooks and rules this installer added"):
            manifest["settings"] = {}
    kept = [CONFIG] + [LEAD / n for n in WORK_DIRS + WORK_FILES]
    if args.purge:
        if not args.yes and not run.dry:
            if not sys.stdin.isatty() or input(f"--purge deletes {short(LEAD)} with the private config, briefs and "
                                               "hand-backs. Type DELETE to go on: ") != "DELETE":
                print("purge skipped (needs --yes, or DELETE typed at the prompt)")
                args.purge = False
        if args.purge:
            run.say("remove", short(LEAD) + "/", "--purge: config, briefs, hand-backs, queue, attention log")
            if not run.dry and LEAD.exists():
                shutil.rmtree(LEAD)
    else:
        for p in kept:
            if p.exists():
                run.say("kept", short(p), "yours; --purge removes it")
    if not run.dry:
        if MANIFEST.exists():
            MANIFEST.unlink()
        for d in [LEAD / "dashboard", LEAD / "rules", LEAD / "bin", CLAUDE / "hooks", CLAUDE / "agents"] + \
                 [CLAUDE / "skills" / s.parent.name for s in (REPO / "skills").glob("*/SKILL.md")]:
            for cache in list(d.rglob("__pycache__")) if d.is_dir() else []:
                shutil.rmtree(cache, ignore_errors=True)
            for sub in sorted([x for x in d.rglob("*") if x.is_dir()], reverse=True) + [d] if d.is_dir() else []:
                try:
                    sub.rmdir()  # only when empty
                except OSError:
                    pass
    print(f"{'dry run' if run.dry else 'uninstall'}: {run.summary()}")
    for p in run.problems:
        print("attention:", p)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print every action, write nothing")
    ap.add_argument("--yes", action="store_true", help="write settings.json without asking (the diff is still printed)")
    ap.add_argument("--force", action="store_true", help="replace files that differ and are not this installer's (backed up)")
    ap.add_argument("--config", metavar="FILE", help="validate FILE and install it as ~/.claude/lead/config.json")
    ap.add_argument("--validate", metavar="FILE", help="only validate a config file")
    ap.add_argument("--check", action="store_true", help="exit 1 if the installed files differ from this repo")
    ap.add_argument("--uninstall", action="store_true", help="remove what this script installed")
    ap.add_argument("--purge", action="store_true", help="with --uninstall: also remove the private config and working folders")
    args = ap.parse_args()
    if args.validate:
        cfg = read_config(Path(args.validate).expanduser())
        left = placeholders(cfg)
        print(f"{args.validate}: usable" + (f"; still holds example values ({', '.join(left)})" if left else ""))
        return 0
    if args.check:
        return check(args)
    if args.uninstall:
        return uninstall(args)
    if args.purge:
        ap.error("--purge only goes with --uninstall")
    return install(args)


if __name__ == "__main__":
    sys.exit(main())
