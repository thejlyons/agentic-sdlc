#!/bin/bash
# Live version as of 2026-11-16, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
# Limits and repos come from ~/.claude/lead/machine.env, which bootstrap writes from config.json (`machine`).
# The defaults below are the live machine's (a 16 GB Mac mini).
[ -f "${LEAD_DIR:-$HOME/.claude/lead}/machine.env" ] && . "${LEAD_DIR:-$HOME/.claude/lead}/machine.env"
: "${STOP_SWAP_MB:=13312}" "${STOP_LOAD:=30}" "${STOP_MIN_FREE_PCT:=15}" "${STOP_GRACE_S:=300}"
# Stop rule for a running simulator job. Run it every 2 minutes during a simulator run and keep the lines.
# A reading is BAD when swap is over 13 GB AND the Mac is under real pressure (1-minute load over 30, or free
# memory under 15%) (J, 2026-11-11: swap alone misleads, an erased simulator's first boot parks ~11 GB there).
# STOP (exit 1) only when two readings in a row are bad, 90 seconds to 10 minutes apart (J, 2026-11-12): a cold
# boot alone tripped the single-reading rule at 09:13 (load 119, swap 14.1 GB, 33% free) and was back to swap
# 7.4 GB and 76% free a minute later, and CI's own cold boot runs at 15 GB swap and passes.
# A first bad reading prints "bad 1 of 2" and exits 0; run it again in 2 minutes.
# Readings in the first 5 minutes after a simulator boots are not counted (J, 2026-11-13): a cold boot alone
# tripped the two-readings rule at 13:37 and 13:39 (load 116 then 33 and falling, 33% then 46% free), and the
# staged start already holds every build until load is under 15, so a boot spike never overlaps a test.
state="${LEAD_DIR:-$HOME/.claude/lead}/.macstop_last_bad"
grace=$STOP_GRACE_S
youngest=$(ps -Ao etime=,comm= | awk '$2 ~ /launchd_sim$/ {
  n = split($1, p, /[-:]/); s = 0
  if ($1 ~ /-/) s = p[1]*86400 + p[2]*3600 + p[3]*60 + p[4]
  else if (n == 3) s = p[1]*3600 + p[2]*60 + p[3]
  else s = p[1]*60 + p[2]
  if (min == "" || s < min) min = s
} END { print (min == "" ? -1 : min) }')
l=$(uptime | sed 's/.*load averages*: //' | awk '{print $1}' | tr -d ,)
sw=$(sysctl -n vm.swapusage | sed 's/.*used = \([0-9.]*\)M.*/\1/')
free=$(memory_pressure 2>/dev/null | sed -n 's/.*free percentage: \([0-9]*\)%.*/\1/p')
free=${free:-100}
now=$(date +%s)
line="$(date +%H:%M) load=$l swapMB=$sw memFree=${free}%"
if [ "$youngest" -ge 0 ] && [ "$youngest" -lt "$grace" ]; then
  echo "$line (a simulator booted ${youngest}s ago: not counted for the first ${grace}s)"
  exit 0
fi
if awk -v l="$l" -v s="$sw" -v f="$free" -v ss="$STOP_SWAP_MB" -v sl="$STOP_LOAD" -v sf="$STOP_MIN_FREE_PCT" 'BEGIN{exit (s>ss && (l>sl || f<sf)) ? 0 : 1}'; then
  last=$(cat "$state" 2>/dev/null || echo 0)
  age=$((now - last))
  if [ "$age" -ge 90 ] && [ "$age" -le 600 ]; then
    echo "$line bad 2 of 2 (previous bad reading ${age}s ago): STOP"
    exit 1
  fi
  # Inside 90 s the earlier bad reading still stands as the first; otherwise this one starts a new pair.
  [ "$age" -lt 90 ] || echo "$now" > "$state"
  echo "$line bad 1 of 2: read again in 2 minutes"
  exit 0
fi
rm -f "$state"
echo "$line"
exit 0
