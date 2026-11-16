#!/bin/bash
# Live version as of 2026-11-16, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
until "$(dirname "$0")/macgate.sh"; do sleep 180; done
date +%H:%M
