#!/bin/bash
# Build a local preview of the dashboard page in a temp folder and print how to open it.
# usage: preview.sh [site-dir] [seed-dir]   (defaults: this repo's site/ and seed/)
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
site="${1:-$here/site}"
seed="${2:-$here/seed}"
out="$(mktemp -d)"
cp "$site"/index.html "$site"/app.js "$site"/logic.js "$out"/
cp "$seed"/*.js "$out"/
cp "$here/preview/stub.js" "$out"/
# The stub must load before app.js asks for the database.
python3 - "$out/index.html" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
tag = '<script src="logic.js"></script>'
if tag not in s:
    sys.exit("index.html no longer loads logic.js with a plain script tag: update preview.sh")
open(p, "w", encoding="utf-8").write(s.replace(tag, '<script src="stub.js"></script>' + tag, 1))
PY
echo "preview in $out"
echo "serve it:  (cd $out && python3 -m http.server 8765)   then open http://localhost:8765/index.html"
