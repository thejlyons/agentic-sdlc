#!/usr/bin/env python3
"""Write the example data for the made-up app FieldApp. Every card here is invented.

Outputs (all committed, so nobody has to run this; run it again only to change the example):
  seed/fld_seed.js                       window.FLD_SEED, in the shape `roadmap_card.py seed` writes
  seed/mirror.js                         an empty, valid window.ROADMAP_MIRROR
  example-vault/Roadmaps/FieldApp/*.md   four of the same cards as vault markdown

Times are fixed so the files do not change between runs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASH = HERE.parent
sys.path.insert(0, str(DASH))
import roadmap_card as rc  # noqa: E402

MADE_AT = "2026-11-16T18:00:00Z"
VAULT_CARDS = ["FLD-3", "FLD-5", "FLD-6", "FLD-8"]


def card(n, title, stage, status, *, area, type_="Feature", size="M", priority="P2", pr="", needs_j=False,
         notes, done_when, history, created, comments=(), **extra):
    boxes = "\n".join(f"- [{'x' if ticked else ' '}] {text}" for ticked, text in done_when)
    doc = {
        "id": f"FLD-{n}", "app": "FieldApp", "title": title, "stage": stage, "area": area, "type": type_,
        "size": size, "priority": priority, "status": status, "needs_j": needs_j, "pr": pr,
        "created": created, "tags": ["card"],
        "body": f"\n# {title}\n\n{notes}\n\n## Done when\n{boxes}\n",
        "comments": list(comments),
        "history": [{"status": s, "at": at, "by": by, "note": note} for s, at, by, note in history],
        "updated": history[-1][1], "updated_by": history[-1][2], "source": {},
    }
    doc.update(extra)
    return doc


CARDS = [
    card(1, "Project list and create flow", "0 Free build", "Released", area="App", pr="3", created="2026-10-20",
         notes="First screen of the app: a list of projects and a sheet to add one.",
         done_when=[(True, "A new project shows in the list after the sheet closes (UI test)."),
                    (True, "Pictures in light, dark and the largest text size.")],
         history=[("Backlog", "2026-10-20T15:02:11Z", "claude", "filed: first build"),
                  ("In progress", "2026-10-21T09:14:40Z", "claude", "worker fld-1, branch fld-1-project-list"),
                  ("In review", "2026-10-21T13:30:05Z", "claude", "PR #3 into dev"),
                  ("Done", "2026-10-21T13:52:48Z", "claude", "squash-merged; review PASS, round 2"),
                  ("Released", "2026-10-28T17:20:19Z", "claude", "Released with #9")]),
    card(2, "Records are stored offline", "0 Free build", "Released", area="Core", size="L", priority="P1", pr="5",
         created="2026-10-20",
         notes="Records save to the local store and survive a relaunch without a network.",
         done_when=[(True, "A record written in flight mode is there after a relaunch (unit and UI test)."),
                    (True, "A store migration test from the first schema.")],
         history=[("Backlog", "2026-10-20T15:03:30Z", "claude", "filed: first build"),
                  ("In progress", "2026-10-22T08:05:12Z", "claude", "worker fld-2, branch fld-2-offline-store"),
                  ("In review", "2026-10-22T16:41:09Z", "claude", "PR #5 into dev"),
                  ("Done", "2026-10-22T17:03:57Z", "claude", "squash-merged; review PASS, round 3"),
                  ("Released", "2026-10-28T17:20:19Z", "claude", "Released with #9")]),
    card(3, "Export a project as CSV", "1 Free build", "Done", area="App", pr="12", created="2026-11-02",
         notes="2026-11-12: merged. Share sheet offers a CSV of every record in the project.",
         done_when=[(True, "The file has one row per record and a header row (unit test on the writer)."),
                    (True, "Commas, quotes and line breaks in a note are escaped (unit test)."),
                    (True, "Pictures of the share sheet in light and dark.")],
         history=[("Backlog", "2026-11-02T10:11:00Z", "claude", "filed: asked for in the first build review"),
                  ("In progress", "2026-11-12T03:10:44Z", "claude", "worker fld-3, branch fld-3-csv-export"),
                  ("In review", "2026-11-12T06:48:21Z", "claude", "PR #12 into dev"),
                  ("Done", "2026-11-12T07:01:33Z", "claude", "squash-merged; review PASS, round 2")]),
    card(4, "Record editor at the largest text size", "1 Free build", "In review", area="App", type_="Bug",
         size="S", priority="P1", pr="14", created="2026-11-10",
         notes="2026-11-16: PR open, waiting for fast CI. Field labels were cut at the largest text size.",
         done_when=[(True, "No label is cut with a long two-word name (UI test shown failing on the old layout)."),
                    (False, "Pictures at the largest text size in light and dark, read by the reviewer.")],
         history=[("Backlog", "2026-11-10T19:22:08Z", "claude", "filed: found in the FLD-3 review"),
                  ("In progress", "2026-11-16T09:02:15Z", "claude", "worker fld-4, branch fld-4-editor-large-text"),
                  ("In review", "2026-11-16T15:40:52Z", "claude", "PR #14 into dev")]),
    card(5, "Map fits every point of the project", "1 Free build", "In progress", area="Map", created="2026-11-11",
         notes="2026-11-16: worker running; code review before the first simulator slot.",
         done_when=[(False, "Opening the map shows every point inside the visible area (frame assertion in a UI test)."),
                    (False, "Pictures on phone and tablet, light and dark.")],
         history=[("Backlog", "2026-11-11T08:15:00Z", "claude", "filed: points near the edge were hidden"),
                  ("Next", "2026-11-15T21:30:10Z", "claude", "queued after FLD-4"),
                  ("In progress", "2026-11-16T16:05:37Z", "claude", "worker fld-5, branch fld-5-map-fit")]),
    card(6, "Empty state for a new project", "1 Free build", "Next", area="App", size="S", needs_j=True,
         created="2026-11-13",
         notes="Question for J (2026-11-16): the empty project can show (A) one line of text and an Add button, or "
               "(B) a short three-step guide. Both are built; pictures are in the gallery. Recommendation: A, "
               "because B repeats the first-run tour.",
         done_when=[(False, "A new project shows the chosen empty state (UI test)."),
                    (False, "Pictures in light, dark and the largest text size.")],
         history=[("Backlog", "2026-11-13T11:00:00Z", "claude", "filed: a new project opened on a blank list"),
                  ("Next", "2026-11-16T14:12:29Z", "claude", "both options built; question for J on the card")]),
    card(7, "Record list sort order", "1 Free build", "Done", area="App", size="S", pr="13", created="2026-11-12",
         notes="2026-11-14: merged with newest first. Decided by the lead after 15 minutes; J can ask for a change.",
         done_when=[(True, "The list is ordered newest first (order assertion shown failing on the old order)."),
                    (True, "The order survives a relaunch (UI test).")],
         history=[("Backlog", "2026-11-12T07:30:00Z", "claude", "filed: follow-up from FLD-3"),
                  ("In progress", "2026-11-14T02:00:41Z", "claude", "worker fld-7, branch fld-7-list-order"),
                  ("In review", "2026-11-14T04:26:03Z", "claude", "PR #13 into dev"),
                  ("Done", "2026-11-14T04:38:50Z", "claude", "squash-merged; review PASS, round 1")],
         lead_decided={"at": "2026-11-14T02:20:00Z", "question": "Newest first or oldest first in the record list?",
                       "choice": "Newest first: the record just added stays in view."}),
    card(8, "Store listing screenshots", "2 Paid", "Backlog", area="Release", type_="Chore", priority="P3",
         created="2026-11-05",
         notes="Waits for the paid developer program. The screenshot tour already runs in CI.",
         done_when=[(False, "One screenshot set per device size from the tour."),
                    (False, "First real upload shows every size accepted.")],
         history=[("Backlog", "2026-11-05T12:00:00Z", "claude", "filed: split from the release checklist")]),
]

NOTE = ("// EXAMPLE DATA. FieldApp and every card in this file are invented, to show the document shape\n"
        "// and to let the page and the tests run. Written by seed/make_example.py; see RESTORE.md.\n")


def main() -> int:
    seed = {"vault_commit": "example", "vault_commit_at": MADE_AT, "made_at": MADE_AT, "cards": CARDS}
    (HERE / "fld_seed.js").write_text(NOTE + "window.FLD_SEED = " + json.dumps(seed, ensure_ascii=False, indent=1) + ";\n",
                                      encoding="utf-8")
    mirror = {"synced_at": MADE_AT, "vault_commit": "example", "vault_commit_at": MADE_AT, "apps": [], "cards": []}
    (HERE / "mirror.js").write_text(
        "// EXAMPLE: an empty mirror. sync_vault.py writes the real one for apps whose cards stay in a markdown vault.\n"
        "window.ROADMAP_MIRROR = " + json.dumps(mirror) + ";\n", encoding="utf-8")
    vault = DASH / "example-vault" / "Roadmaps" / "FieldApp"
    vault.mkdir(parents=True, exist_ok=True)
    for old in vault.glob("*.md"):
        old.unlink()
    for c in CARDS:
        if c["id"] in VAULT_CARDS:
            (vault / f"{c['id']} {c['title']}.md").write_text(rc.card_to_md(c), encoding="utf-8")
    print(f"wrote {len(CARDS)} seed cards, an empty mirror and {len(VAULT_CARDS)} vault cards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
