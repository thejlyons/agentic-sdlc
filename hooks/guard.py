#!/usr/bin/env python3
# Live version as of 2026-11-16, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
"""PreToolUse guard for Bash (the studio lead loop).

Prints a permission decision only when a rule matches; otherwise stays silent so
the normal permission flow (and auto mode's classifier) decides.

deny : anything touching a protected folder (guardrails.protected_paths in ~/.claude/lead/config.json;
       example ~/Protected); force-push to main or dev.
ask  : a push to an app repo's main (exempt: the vault's main, for card commits,
       and the public process repo's main, which has no dev branch; J, 2026-11-16);
       `gh pr merge` unless CI is all green AND the PR carries a "Review: PASS"
       comment from a separate reviewer; App Store Connect tooling; deleting
       vault content; deleting repos/releases; publishing a site by hand.

Self-test: guard.py --test
"""
import json
import os
import re
import shlex
import subprocess
import sys

def _guardrails():
    """guardrails from ~/.claude/lead/config.json; the defaults are the example config's."""
    try:
        with open(os.path.expanduser("~/.claude/lead/config.json")) as f:
            return json.load(f).get("guardrails") or {}
    except (OSError, ValueError):
        return {}


_G = _guardrails()
VAULT = _G.get("vault_repo") or "roadmap-vault"
PROTECTED = [os.path.basename(p.rstrip("/")) for p in (_G.get("protected_paths") or ["~/Protected"])] or ["Protected"]
PROCESS_REPO = "agentic-sdlc"  # public process repo: main only, synced by scripts/sync.py (its scan gates the push)
REVIEW_MARK = "Review: PASS"
SEPARATORS = {"&&", "||", ";", "|", "&"}

ASC_RE = re.compile(
    r"\b(altool|notarytool|iTMSTransporter|fastlane|appstoreconnect|app-store-connect)\b"
    r"|\bxcrun\s+(altool|notarytool)\b|-exportArchive\b.*upload|\basc\s",
    re.I,
)
SITE_RE = re.compile(r"\bwrangler\b.*\b(deploy|publish)\b")
GH_DESTRUCT_RE = re.compile(r"\bgh\s+(repo\s+delete|release\s+(create|delete))\b")


def run(args, cwd):
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=20)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def split_segments(cmd):
    """Split a shell command into simple commands (token lists)."""
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        tokens = cmd.split()
    segs, cur = [], []
    for t in tokens:
        if t in SEPARATORS:
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        segs.append(cur)
    return segs


def repo_url(d):
    _, out = run(["git", "-C", d, "remote", "get-url", "origin"], d if os.path.isdir(d) else None)
    return out


def is_vault(d):
    return VAULT in repo_url(d) or VAULT in os.path.abspath(d)


def is_process_repo(d):
    url = repo_url(d).rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    return url.endswith("/" + PROCESS_REPO) or os.path.basename(os.path.abspath(d)) == PROCESS_REPO


def git_parts(seg, cwd):
    """For a `git ...` segment return (dir, subcommand, args) honouring -C and -c."""
    d, i = cwd, 1
    while i < len(seg):
        t = seg[i]
        if t == "-C" and i + 1 < len(seg):
            d = os.path.join(d, os.path.expanduser(seg[i + 1]))
            i += 2
        elif t == "-c" and i + 1 < len(seg):
            i += 2
        elif t.startswith("-"):
            i += 1
        else:
            return d, t, seg[i + 1:]
    return d, "", []


def check_push(d, args):
    force = any(a in ("-f", "--force") or a.startswith("--force-with-lease") or a.startswith("--force-if-includes") for a in args)
    pos = [a for a in args if not a.startswith("-")]
    refspecs = pos[1:]  # pos[0] is the remote
    if any(r.startswith("+") for r in refspecs):
        force = True
    dsts = []
    for r in refspecs:
        r = r.lstrip("+")
        dst = r.split(":", 1)[1] if ":" in r else r
        dsts.append(dst.replace("refs/heads/", ""))
    _, branch = run(["git", "-C", d, "rev-parse", "--abbrev-ref", "HEAD"], None)
    if not refspecs or "HEAD" in dsts:
        dsts = [x for x in dsts if x != "HEAD"] + [branch]
    if "--all" in args or "--mirror" in args:
        dsts += ["main", "dev"]
    if force and any(x in ("main", "dev") for x in dsts):
        return "deny", "Force-push to main or dev is never allowed."
    if "main" in dsts and not is_vault(d) and not is_process_repo(d):
        return "ask", "Direct push to an app repo's main: J must approve (releases go through a dev to main PR)."
    return None


def check_merge(seg, cwd):
    args = seg[3:]
    sel, repo, i = None, None, 0
    while i < len(args):
        a = args[i]
        if a in ("-R", "--repo") and i + 1 < len(args):
            repo = args[i + 1]
            i += 2
        elif a in ("-b", "--body", "-F", "--body-file", "-t", "--subject", "--match-head-commit", "-A", "--author-email") and i + 1 < len(args):
            i += 2
        elif a.startswith("-"):
            i += 1
        else:
            sel = sel or a
            i += 1
    view = ["gh", "pr", "view"] + ([sel] if sel else []) + (["-R", repo] if repo else [])
    view += ["--json", "number,baseRefName,statusCheckRollup,comments,reviews"]
    code, out = run(view, cwd if os.path.isdir(cwd) else None)
    if code != 0:
        return "ask", "Could not read the PR to verify CI and review before merging."
    try:
        pr = json.loads(out)
    except ValueError:
        return "ask", "Could not parse the PR state before merging."
    problems = []
    checks = pr.get("statusCheckRollup") or []
    bad = []
    for c in checks:
        state = (c.get("conclusion") or c.get("state") or c.get("status") or "").upper()
        if state not in ("SUCCESS", "SKIPPED", "NEUTRAL"):
            bad.append("%s=%s" % (c.get("name") or c.get("context") or "check", state or "PENDING"))
    if not checks:
        problems.append("no CI checks reported")
    if bad:
        problems.append("checks not green: " + ", ".join(bad[:4]))
    texts = [c.get("body", "") for c in (pr.get("comments") or [])] + [r.get("body", "") for r in (pr.get("reviews") or [])]
    if not any(REVIEW_MARK in t for t in texts):
        problems.append('no "%s" comment from a separate reviewer' % REVIEW_MARK)
    if problems:
        return "ask", "PR #%s into %s: %s." % (pr.get("number"), pr.get("baseRefName"), "; ".join(problems))
    return None


def decide(cmd, cwd):
    for name in PROTECTED:
        if re.search(r"(~|\$HOME|/Users/[^/\s]+|/home/[^/\s]+)/" + re.escape(name) + r"\b", cmd):
            return "deny", "~/%s is a protected folder: never touch it." % name
    worst = None

    def note(res):
        nonlocal worst
        if res and (worst is None or (res[0] == "deny" and worst[0] != "deny")):
            worst = res

    d = cwd
    for seg in split_segments(cmd):
        while seg and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[0]):
            seg = seg[1:]  # leading VAR=value
        if not seg:
            continue
        if seg[0] == "cd" and len(seg) > 1:
            d = os.path.normpath(os.path.join(d, os.path.expanduser(seg[1])))
            continue
        if seg[0] == "git":
            gd, sub, args = git_parts(seg, d)
            if sub == "push":
                note(check_push(gd, args))
            elif sub in ("rm", "clean") and is_vault(gd):
                note(("ask", "Deleting vault content needs J's approval."))
        elif seg[:3] == ["gh", "pr", "merge"]:
            note(check_merge(seg, d))
        elif seg[0] in ("rm", "rmdir", "trash", "unlink"):
            targets = [a for a in seg[1:] if not a.startswith("-")]
            in_vault = is_vault(d) and not any(os.path.isabs(os.path.expanduser(t)) for t in targets)
            if in_vault or any(VAULT in t for t in targets):
                if not all("/.claude/worktrees/" in os.path.join(d, t) for t in targets):
                    note(("ask", "Deleting vault content needs J's approval."))
    if ASC_RE.search(cmd):
        note(("ask", "App Store Connect / notarization tooling: J must approve."))
    if GH_DESTRUCT_RE.search(cmd):
        note(("ask", "Deleting a repo or creating/deleting a release: J must approve."))
    if SITE_RE.search(cmd):
        note(("ask", "Publishing a site by hand: J must approve (CI deploys normally)."))
    return worst


def selftest():
    home = os.path.expanduser("~")
    app = home + "/Github/studyapp"
    vault = home + "/Github/" + VAULT
    cases = [
        ("git push origin main", app, "ask"),
        ("git push origin HEAD:main", app, "ask"),
        ("git -C %s push origin dev:main" % app, "/tmp", "ask"),
        ("cd %s && git push origin HEAD:main" % app, "/tmp", "ask"),
        ("git push origin HEAD:main", vault, None),
        ("git push origin HEAD:main", home + "/Github/" + PROCESS_REPO, None),
        ("cd %s && git push -q origin HEAD:main" % (home + "/Github/" + PROCESS_REPO), "/tmp", None),
        ("git push --force origin main", home + "/Github/" + PROCESS_REPO, "deny"),
        ("git push origin HEAD:main", home + "/Github/agentic-sdlc-draft", "ask"),
        ("git push --force origin main", vault, "deny"),
        ("git push -f origin dev", app, "deny"),
        ("git push origin +abc:dev", app, "deny"),
        ("git push --force-with-lease origin stu-112-quiet", app, None),
        ("git push -u origin stu-112-quiet", app, None),
        ("git push origin dev", app, None),
        ("rm -rf ~/%s/foo" % PROTECTED[0], app, "deny"),
        ("ls /Users/someone/%s" % PROTECTED[0], app, "deny"),
        ("rm Roadmaps/AppF/APF-1.md", vault, "ask"),
        ("git rm Roadmaps/AppF/APF-1.md", vault, "ask"),
        ("rm -rf build", app, None),
        ("xcrun altool --upload-app -f x.ipa", app, "ask"),
        ("gh release create v1", app, "ask"),
        ("npx wrangler pages deploy dist", app, "ask"),
        ("git status && swift test", app, None),
        ("echo 'git push origin main'", app, None),
    ]
    failed = 0
    for cmd, cwd, want in cases:
        got = decide(cmd, cwd)
        got = got[0] if got else None
        ok = got == want
        failed += not ok
        print("%s  %-55s want=%s got=%s" % ("ok  " if ok else "FAIL", cmd[:55], want, got))
    sys.exit(1 if failed else 0)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        selftest()
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    cmd = (data.get("tool_input") or {}).get("command") or ""
    res = decide(cmd, data.get("cwd") or os.getcwd())
    if res:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": res[0],
            "permissionDecisionReason": "[guard] " + res[1],
        }}))
    sys.exit(0)


if __name__ == "__main__":
    main()
