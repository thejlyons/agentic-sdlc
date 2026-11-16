#!/usr/bin/env python3
"""Compute the README's numbers from data/*.tsv. Every figure in the README is one of these lines.

data/merged-prs.tsv    one row per PR the lead loop merged into an app's dev branch (merge time from GitHub, card
                       ids from the PR title, review rounds and first verdict from the PR's "Review: PASS" comment).
data/reviewer-runs.tsv one row per reviewer agent run (start time, model, final verdict from its transcript).
Both are written on the owner's machine by a private collector, because the app repos are private.
"""
import csv
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
prs = list(csv.DictReader(open(DATA / "merged-prs.tsv"), delimiter="\t"))
runs = list(csv.DictReader(open(DATA / "reviewer-runs.tsv"), delimiter="\t"))

t = [datetime.fromisoformat(p["merged_utc"].replace("Z", "+00:00")) for p in prs]
days = (max(t) - min(t)).total_seconds() / 86400
cards = sum(int(p["card_count"]) for p in prs)
rounds = [int(p["review_rounds"]) for p in prs]
first = Counter(p["first_review"] for p in prs)
print(f"period: {min(t):%Y-%m-%d %H:%M} to {max(t):%Y-%m-%d %H:%M} UTC ({days:.1f} days), apps: {sorted({p['app'] for p in prs})}")
print(f"PRs merged: {len(prs)} ({len(prs) / days:.1f} per day)")
unique = len({c for p in prs for c in p["cards_in_title"].split()})
print(f"card ids named in those PR titles: {unique} distinct ({unique / days:.1f} per day; {cards} counting a card split over two PRs twice)")
print("PRs merged per UTC day:", dict(sorted(Counter(x.strftime('%m-%d') for x in t).items())))
print(f"review rounds per PR: total {sum(rounds)}, median {statistics.median(rounds)}, mean {statistics.mean(rounds):.1f}, "
      f"max {max(rounds)}; distribution {dict(sorted(Counter(rounds).items()))}")
print(f"first review of each PR: {dict(first)} "
      f"({first['CHANGES']} of {len(prs)} = {100 * first['CHANGES'] / len(prs):.0f}% returned CHANGES)")
v = Counter(r["verdict"] for r in runs)
print(f"reviewer runs: {len(runs)} from {runs[0]['started_utc']} to {runs[-1]['started_utc']}; verdicts {dict(v)} "
      f"({100 * v['CHANGES'] / len(runs):.0f}% CHANGES)")
print("reviewer runs by model and verdict:", dict(sorted(Counter((r['reviewer_model'], r['verdict']) for r in runs).items())))
