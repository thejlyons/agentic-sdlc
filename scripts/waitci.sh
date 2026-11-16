#!/bin/bash
# Live version as of 2026-11-16, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
# wait until the CI run on a branch completes, then print its conclusion
# usage: waitci.sh <branch> [owner/repo]   (the repo defaults to CI_REPO from machine.env)
# Limits and repos come from ~/.claude/lead/machine.env, which bootstrap writes from config.json (`machine`).
# The defaults below are the live machine's (a 16 GB Mac mini).
[ -f "${LEAD_DIR:-$HOME/.claude/lead}/machine.env" ] && . "${LEAD_DIR:-$HOME/.claude/lead}/machine.env"
b="$1"
repo="${2:-${CI_REPO:?give owner/repo as the second argument or set CI_REPO}}"
while true; do
  s=$(gh run list -R "$repo" --branch "$b" --limit 1 --json status -q '.[0].status')
  [ "$s" = "completed" ] && break
  sleep 120
done
gh run list -R "$repo" --branch "$b" --limit 1 --json conclusion,url -q '.[0]'
date +%H:%M
