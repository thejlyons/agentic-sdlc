#!/usr/bin/env bash
# Restore test: install this repo into an empty temporary HOME and check that what lands there works.
# Runs on macOS and Linux (CI). It never touches the real home folder.
#   bash bootstrap/restore_test.sh
# What it cannot test is listed in docs/restore-verification.md.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
REAL_PATH="$PATH"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
export HOME="$T/home"
mkdir -p "$HOME" "$T/bin" "$T/app"
# A stand-in for osascript, so the attention hook shows no desktop notification during the test.
printf '#!/bin/sh\nexit 0\n' > "$T/bin/osascript"
chmod +x "$T/bin/osascript"
export PATH="$T/bin:$REAL_PATH"
unset LEAD_DIR GATE_REPOS CI_REPO 2>/dev/null

pass=0; fail=0; skipped=0
ok()   { pass=$((pass + 1)); echo "ok    $1"; }
bad()  { fail=$((fail + 1)); echo "FAIL  $1"; }
skip() { skipped=$((skipped + 1)); echo "skip  $1"; }
check() { if "${@:2}" >/dev/null 2>&1; then ok "$1"; else bad "$1"; fi; }
sum() { python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }
install() { python3 "$REPO/bootstrap/install.py" "$@"; }
C="$HOME/.claude"; L="$C/lead"

echo "== 1. dry run writes nothing"
install --dry-run --config "$REPO/config/config.example.json" > "$T/dry.log" 2>&1 && ok "dry run exits 0" || bad "dry run exits 0"
[ -z "$(ls -A "$HOME")" ] && ok "home folder still empty after the dry run" || bad "home folder still empty after the dry run"
grep -q "would install" "$T/dry.log" && grep -q "guard.py" "$T/dry.log" && ok "dry run lists the files and the settings diff" || bad "dry run lists the files and the settings diff"

echo "== 2. install without --yes and without a terminal leaves settings alone"
install --config "$REPO/config/config.example.json" < /dev/null > "$T/noyes.log" 2>&1
[ ! -e "$C/settings.json" ] && ok "settings.json not written without consent" || bad "settings.json not written without consent"

echo "== 3. real install, twice"
install --yes --config "$REPO/config/config.example.json" > "$T/install1.log" 2>&1 && ok "install exits 0" || { bad "install exits 0"; cat "$T/install1.log"; }
install --yes > "$T/install2.log" 2>&1 && ok "second install exits 0" || bad "second install exits 0"
if grep -Eq "^(install|update|replace|write|create|merge) " "$T/install2.log"; then bad "second install changes nothing"; else ok "second install changes nothing"; fi

echo "== 4. every file landed and equals the repo's"
n=0; wrong=0
while IFS= read -r pair; do
  src="${pair%%|*}"; dest="${pair##*|}"; n=$((n + 1))
  if [ ! -f "$dest" ] || [ "$(sum "$src")" != "$(sum "$dest")" ]; then wrong=$((wrong + 1)); echo "      differs or missing: $dest"; fi
done < <(
  cd "$REPO" || exit 1
  for f in skills/*/SKILL.md; do echo "$REPO/$f|$C/$f"; done
  for f in agents/*.md; do echo "$REPO/$f|$C/$f"; done
  for f in guard.py attention.py; do echo "$REPO/hooks/$f|$C/hooks/$f"; done
  for f in macgate.sh macstop.sh waitgate.sh waitci.sh; do echo "$REPO/scripts/$f|$L/bin/$f"; done
  find dashboard rules -type f ! -path '*/__pycache__/*' ! -path 'dashboard/out/*' ! -name '*.pyc' ! -name '.DS_Store' 2>/dev/null |
    while IFS= read -r f; do echo "$REPO/$f|$L/$f"; done
)
[ "$wrong" -eq 0 ] && [ "$n" -gt 20 ] && ok "$n installed files match the repo by checksum" || bad "$wrong of $n installed files differ or are missing"
for s in lead-loop back-to-work bootstrap; do check "skill $s installed" test -f "$C/skills/$s/SKILL.md"; done
for a in card-implementer card-reviewer; do check "agent $a installed" test -f "$C/agents/$a.md"; done
for d in briefs handbacks research; do check "working folder $d" test -d "$L/$d"; done
for f in queue.md attention.jsonl config.json machine.env .install-manifest.json; do check "file $f" test -f "$L/$f"; done
for f in macgate.sh macstop.sh waitgate.sh waitci.sh; do check "$f is executable" test -x "$L/bin/$f"; done

echo "== 5. settings.json"
python3 - "$C/settings.json" <<'PY' && ok "both hooks present exactly once after two installs; allow rules not doubled" || bad "settings hooks or rules wrong after two installs"
import json, sys
s = json.load(open(sys.argv[1]))
cmds = lambda ev: [h["command"] for g in s["hooks"][ev] for h in g["hooks"]]
assert sum("hooks/guard.py" in c for c in cmds("PreToolUse")) == 1, cmds("PreToolUse")
assert sum("hooks/attention.py" in c for c in cmds("Notification")) == 1, cmds("Notification")
assert s["hooks"]["PreToolUse"][0]["matcher"] == "Bash"
allow = s["permissions"]["allow"]
assert len(allow) == len(set(allow)) and any(a.endswith("/.claude/lead/bin/macgate.sh)") for a in allow)
assert not any("~/" in a for a in allow)
PY
# An existing settings file must be merged, not replaced.
H2="$T/home2"; mkdir -p "$H2/.claude"
printf '{"model": "keep-me", "permissions": {"allow": ["Bash(echo *)"]}, "hooks": {"PreToolUse": [{"matcher": "Write", "hooks": [{"type": "command", "command": "true"}]}]}}\n' > "$H2/.claude/settings.json"
HOME="$H2" python3 "$REPO/bootstrap/install.py" --yes > "$T/merge.log" 2>&1
python3 - "$H2/.claude" <<'PY' && ok "an existing settings.json keeps its own entries, gains ours, and is backed up" || bad "merge into an existing settings.json"
import glob, json, sys
s = json.load(open(sys.argv[1] + "/settings.json"))
assert s["model"] == "keep-me" and "Bash(echo *)" in s["permissions"]["allow"]
pre = s["hooks"]["PreToolUse"]
assert pre[0]["matcher"] == "Write" and any("guard.py" in h["command"] for g in pre for h in g["hooks"])
assert glob.glob(sys.argv[1] + "/settings.json.bak-*")
PY
grep -q '^+' "$T/merge.log" && ok "the settings diff was printed" || bad "the settings diff was printed"

echo "== 6. machine.env from the example config"
( . "$L/machine.env"
  [ "$GATE_MAX_LOAD" = 30 ] && [ "$GATE_MAX_SWAP_MB" = 12288 ] && [ "$GATE_REPOS" = "OWNER/fieldapp OWNER/studyapp" ] &&
  [ "$STOP_SWAP_MB" = 13312 ] && [ "$STOP_LOAD" = 30 ] && [ "$STOP_MIN_FREE_PCT" = 15 ] && [ "$STOP_GRACE_S" = 300 ] &&
  [ "$CI_REPO" = "OWNER/fieldapp" ] ) && ok "machine.env holds the config's limits and repos" || bad "machine.env values"
printf '{"owner": {}}' > "$T/bad.json"
if install --validate "$T/bad.json" >/dev/null 2>&1; then bad "a broken config is refused"; else ok "a broken config is refused"; fi

echo "== 7. scripts parse"
for f in macgate.sh macstop.sh waitgate.sh waitci.sh; do check "bash -n $f" bash -n "$L/bin/$f"; done
if [ "$(uname)" = Darwin ]; then
  out="$(PATH="$REAL_PATH" bash "$L/bin/macstop.sh" 2>&1)"; rc=$?
  echo "$out" | grep -Eq 'load=[0-9.]+ swapMB=[0-9.]+ memFree=[0-9]+%' && [ "$rc" -le 1 ] && ok "macstop.sh prints a reading on this Mac ($out)" || bad "macstop.sh reading: $out"
else
  skip "macstop.sh reading (reads macOS memory counters; parse check only on $(uname))"
fi

echo "== 8. guard hook"
check "guard.py --test (its own 21 cases)" python3 "$C/hooks/guard.py" --test
guard() { printf '{"tool_name": "Bash", "tool_input": {"command": "%s"}, "cwd": "%s"}' "$1" "$T/app" | python3 "$C/hooks/guard.py"; }
guard "git push origin main" | grep -q '"permissionDecision": "ask"' && ok "guard asks: git push origin main in an app folder" || bad "guard asks on a push to main"
guard "rm -rf ~/Protected/x" | grep -q '"permissionDecision": "deny"' && ok "guard denies: rm -rf under the protected path of the config" || bad "guard denies the protected path"
[ -z "$(guard "git status")" ] && ok "guard stays silent: git status" || bad "guard silent on git status"
[ -z "$(printf '{"tool_name": "Read", "tool_input": {"file_path": "x"}}' | python3 "$C/hooks/guard.py")" ] && ok "guard ignores tools other than Bash" || bad "guard ignores other tools"

echo "== 9. attention hook"
before=$(wc -l < "$L/attention.jsonl")
printf '{"notification_type": "permission_prompt", "session_id": "test-session", "cwd": "%s", "message": "Claude needs your permission to use Bash"}' "$T/app" | python3 "$C/hooks/attention.py"; rc=$?
after=$(wc -l < "$L/attention.jsonl")
[ "$rc" -eq 0 ] && [ "$after" -eq $((before + 1)) ] && grep -q '"session": "test-session"' "$L/attention.jsonl" && ok "a permission prompt is logged to attention.jsonl" || bad "attention hook log line"
printf '{"notification_type": "something_else"}' | python3 "$C/hooks/attention.py"
[ "$(wc -l < "$L/attention.jsonl")" -eq "$after" ] && ok "other notification types are not logged" || bad "attention hook filters types"
mkdir -p "$T/empty"
printf '{"notification_type": "idle_prompt"}' | PATH="$T/empty" "$(command -v python3)" "$C/hooks/attention.py" && ok "attention hook exits 0 when it cannot show a notification" || bad "attention hook without a notifier"

echo "== 10. dashboard tools"
python3 "$L/dashboard/roadmap_card.py" new --app FieldApp --id FLD-900 --title "Restore test" --stage "1 Free build" --note test 2>/dev/null |
  grep -q '"path": "fld/FLD-900"' && ok "roadmap_card.py builds a new-card op" || bad "roadmap_card.py new"
if command -v node >/dev/null 2>&1 && [ "$(node -p 'Number(process.versions.node.split(".")[0]) >= 18')" = true ]; then
  if node --test "$L"/dashboard/tests/*.test.js > "$T/node.log" 2>&1; then
    ok "dashboard tests pass from the installed copy ($(grep -E '^. pass ' "$T/node.log" | tr -dc '0-9') passed, $(grep -E '^. skipped ' "$T/node.log" | tr -dc '0-9') skipped for want of private data)"
  else bad "dashboard tests from the installed copy"; tail -20 "$T/node.log"; fi
else
  skip "dashboard tests (node 18 or newer not found)"
fi

echo "== 11. check, an owner-edited file, uninstall"
check "install.py --check passes" install --check
echo "# my own note" >> "$C/agents/card-reviewer.md"
if install --check >/dev/null 2>&1; then bad "--check notices an edited file"; else ok "--check notices an edited file"; fi
install --uninstall --dry-run > "$T/undry.log" 2>&1
check "uninstall dry run removes nothing" test -f "$C/hooks/guard.py"
install --uninstall --yes > "$T/uninstall.log" 2>&1 && ok "uninstall exits 0" || bad "uninstall exits 0"
gone=1; for f in "$C/hooks/guard.py" "$C/hooks/attention.py" "$C/skills/lead-loop/SKILL.md" "$C/agents/card-implementer.md" "$L/bin/macgate.sh" "$L/dashboard/roadmap_card.py" "$L/machine.env" "$L/.install-manifest.json"; do [ -e "$f" ] && { gone=0; echo "      still there: $f"; }; done
[ "$gone" -eq 1 ] && ok "installed files are gone" || bad "installed files are gone"
check "the edited file was left in place" grep -q "my own note" "$C/agents/card-reviewer.md"
python3 - "$C/settings.json" <<'PY' && ok "settings.json no longer has the hooks or the rules" || bad "settings.json after uninstall"
import json, sys
s = json.load(open(sys.argv[1]))
assert "guard.py" not in json.dumps(s) and "attention.py" not in json.dumps(s) and "macgate" not in json.dumps(s), s
PY
kept=1; for f in "$L/config.json" "$L/queue.md" "$L/attention.jsonl" "$L/briefs" "$L/handbacks" "$L/research"; do [ -e "$f" ] || { kept=0; echo "      lost: $f"; }; done
[ "$kept" -eq 1 ] && ok "config, queue, attention log and working folders are kept" || bad "private files kept on uninstall"
install --uninstall --purge --yes > /dev/null 2>&1
[ ! -e "$L" ] && ok "--purge removes the private folder" || bad "--purge removes the private folder"

echo
echo "restore test on $(uname -s): $pass passed, $fail failed, $skipped skipped (python $(python3 -c 'import platform; print(platform.python_version())'), node $(command -v node >/dev/null 2>&1 && node --version || echo none))"
[ "$fail" -eq 0 ]
