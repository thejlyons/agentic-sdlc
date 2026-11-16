// EXAMPLE DATA. FieldApp and every card in this file are invented, to show the document shape
// and to let the page and the tests run. Written by seed/make_example.py; see RESTORE.md.
window.FLD_SEED = {
 "vault_commit": "example",
 "vault_commit_at": "2026-11-16T18:00:00Z",
 "made_at": "2026-11-16T18:00:00Z",
 "cards": [
  {
   "id": "FLD-1",
   "app": "FieldApp",
   "title": "Project list and create flow",
   "stage": "0 Free build",
   "area": "App",
   "type": "Feature",
   "size": "M",
   "priority": "P2",
   "status": "Released",
   "needs_j": false,
   "pr": "3",
   "created": "2026-10-20",
   "tags": [
    "card"
   ],
   "body": "\n# Project list and create flow\n\nFirst screen of the app: a list of projects and a sheet to add one.\n\n## Done when\n- [x] A new project shows in the list after the sheet closes (UI test).\n- [x] Pictures in light, dark and the largest text size.\n",
   "comments": [],
   "history": [
    {
     "status": "Backlog",
     "at": "2026-10-20T15:02:11Z",
     "by": "claude",
     "note": "filed: first build"
    },
    {
     "status": "In progress",
     "at": "2026-10-21T09:14:40Z",
     "by": "claude",
     "note": "worker fld-1, branch fld-1-project-list"
    },
    {
     "status": "In review",
     "at": "2026-10-21T13:30:05Z",
     "by": "claude",
     "note": "PR #3 into dev"
    },
    {
     "status": "Done",
     "at": "2026-10-21T13:52:48Z",
     "by": "claude",
     "note": "squash-merged; review PASS, round 2"
    },
    {
     "status": "Released",
     "at": "2026-10-28T17:20:19Z",
     "by": "claude",
     "note": "Released with #9"
    }
   ],
   "updated": "2026-10-28T17:20:19Z",
   "updated_by": "claude",
   "source": {}
  },
  {
   "id": "FLD-2",
   "app": "FieldApp",
   "title": "Records are stored offline",
   "stage": "0 Free build",
   "area": "Core",
   "type": "Feature",
   "size": "L",
   "priority": "P1",
   "status": "Released",
   "needs_j": false,
   "pr": "5",
   "created": "2026-10-20",
   "tags": [
    "card"
   ],
   "body": "\n# Records are stored offline\n\nRecords save to the local store and survive a relaunch without a network.\n\n## Done when\n- [x] A record written in flight mode is there after a relaunch (unit and UI test).\n- [x] A store migration test from the first schema.\n",
   "comments": [],
   "history": [
    {
     "status": "Backlog",
     "at": "2026-10-20T15:03:30Z",
     "by": "claude",
     "note": "filed: first build"
    },
    {
     "status": "In progress",
     "at": "2026-10-22T08:05:12Z",
     "by": "claude",
     "note": "worker fld-2, branch fld-2-offline-store"
    },
    {
     "status": "In review",
     "at": "2026-10-22T16:41:09Z",
     "by": "claude",
     "note": "PR #5 into dev"
    },
    {
     "status": "Done",
     "at": "2026-10-22T17:03:57Z",
     "by": "claude",
     "note": "squash-merged; review PASS, round 3"
    },
    {
     "status": "Released",
     "at": "2026-10-28T17:20:19Z",
     "by": "claude",
     "note": "Released with #9"
    }
   ],
   "updated": "2026-10-28T17:20:19Z",
   "updated_by": "claude",
   "source": {}
  },
  {
   "id": "FLD-3",
   "app": "FieldApp",
   "title": "Export a project as CSV",
   "stage": "1 Free build",
   "area": "App",
   "type": "Feature",
   "size": "M",
   "priority": "P2",
   "status": "Done",
   "needs_j": false,
   "pr": "12",
   "created": "2026-11-02",
   "tags": [
    "card"
   ],
   "body": "\n# Export a project as CSV\n\n2026-11-12: merged. Share sheet offers a CSV of every record in the project.\n\n## Done when\n- [x] The file has one row per record and a header row (unit test on the writer).\n- [x] Commas, quotes and line breaks in a note are escaped (unit test).\n- [x] Pictures of the share sheet in light and dark.\n",
   "comments": [],
   "history": [
    {
     "status": "Backlog",
     "at": "2026-11-02T10:11:00Z",
     "by": "claude",
     "note": "filed: asked for in the first build review"
    },
    {
     "status": "In progress",
     "at": "2026-11-12T03:10:44Z",
     "by": "claude",
     "note": "worker fld-3, branch fld-3-csv-export"
    },
    {
     "status": "In review",
     "at": "2026-11-12T06:48:21Z",
     "by": "claude",
     "note": "PR #12 into dev"
    },
    {
     "status": "Done",
     "at": "2026-11-12T07:01:33Z",
     "by": "claude",
     "note": "squash-merged; review PASS, round 2"
    }
   ],
   "updated": "2026-11-12T07:01:33Z",
   "updated_by": "claude",
   "source": {}
  },
  {
   "id": "FLD-4",
   "app": "FieldApp",
   "title": "Record editor at the largest text size",
   "stage": "1 Free build",
   "area": "App",
   "type": "Bug",
   "size": "S",
   "priority": "P1",
   "status": "In review",
   "needs_j": false,
   "pr": "14",
   "created": "2026-11-10",
   "tags": [
    "card"
   ],
   "body": "\n# Record editor at the largest text size\n\n2026-11-16: PR open, waiting for fast CI. Field labels were cut at the largest text size.\n\n## Done when\n- [x] No label is cut with a long two-word name (UI test shown failing on the old layout).\n- [ ] Pictures at the largest text size in light and dark, read by the reviewer.\n",
   "comments": [],
   "history": [
    {
     "status": "Backlog",
     "at": "2026-11-10T19:22:08Z",
     "by": "claude",
     "note": "filed: found in the FLD-3 review"
    },
    {
     "status": "In progress",
     "at": "2026-11-16T09:02:15Z",
     "by": "claude",
     "note": "worker fld-4, branch fld-4-editor-large-text"
    },
    {
     "status": "In review",
     "at": "2026-11-16T15:40:52Z",
     "by": "claude",
     "note": "PR #14 into dev"
    }
   ],
   "updated": "2026-11-16T15:40:52Z",
   "updated_by": "claude",
   "source": {}
  },
  {
   "id": "FLD-5",
   "app": "FieldApp",
   "title": "Map fits every point of the project",
   "stage": "1 Free build",
   "area": "Map",
   "type": "Feature",
   "size": "M",
   "priority": "P2",
   "status": "In progress",
   "needs_j": false,
   "pr": "",
   "created": "2026-11-11",
   "tags": [
    "card"
   ],
   "body": "\n# Map fits every point of the project\n\n2026-11-16: worker running; code review before the first simulator slot.\n\n## Done when\n- [ ] Opening the map shows every point inside the visible area (frame assertion in a UI test).\n- [ ] Pictures on phone and tablet, light and dark.\n",
   "comments": [],
   "history": [
    {
     "status": "Backlog",
     "at": "2026-11-11T08:15:00Z",
     "by": "claude",
     "note": "filed: points near the edge were hidden"
    },
    {
     "status": "Next",
     "at": "2026-11-15T21:30:10Z",
     "by": "claude",
     "note": "queued after FLD-4"
    },
    {
     "status": "In progress",
     "at": "2026-11-16T16:05:37Z",
     "by": "claude",
     "note": "worker fld-5, branch fld-5-map-fit"
    }
   ],
   "updated": "2026-11-16T16:05:37Z",
   "updated_by": "claude",
   "source": {}
  },
  {
   "id": "FLD-6",
   "app": "FieldApp",
   "title": "Empty state for a new project",
   "stage": "1 Free build",
   "area": "App",
   "type": "Feature",
   "size": "S",
   "priority": "P2",
   "status": "Next",
   "needs_j": true,
   "pr": "",
   "created": "2026-11-13",
   "tags": [
    "card"
   ],
   "body": "\n# Empty state for a new project\n\nQuestion for J (2026-11-16): the empty project can show (A) one line of text and an Add button, or (B) a short three-step guide. Both are built; pictures are in the gallery. Recommendation: A, because B repeats the first-run tour.\n\n## Done when\n- [ ] A new project shows the chosen empty state (UI test).\n- [ ] Pictures in light, dark and the largest text size.\n",
   "comments": [],
   "history": [
    {
     "status": "Backlog",
     "at": "2026-11-13T11:00:00Z",
     "by": "claude",
     "note": "filed: a new project opened on a blank list"
    },
    {
     "status": "Next",
     "at": "2026-11-16T14:12:29Z",
     "by": "claude",
     "note": "both options built; question for J on the card"
    }
   ],
   "updated": "2026-11-16T14:12:29Z",
   "updated_by": "claude",
   "source": {}
  },
  {
   "id": "FLD-7",
   "app": "FieldApp",
   "title": "Record list sort order",
   "stage": "1 Free build",
   "area": "App",
   "type": "Feature",
   "size": "S",
   "priority": "P2",
   "status": "Done",
   "needs_j": false,
   "pr": "13",
   "created": "2026-11-12",
   "tags": [
    "card"
   ],
   "body": "\n# Record list sort order\n\n2026-11-14: merged with newest first. Decided by the lead after 15 minutes; J can ask for a change.\n\n## Done when\n- [x] The list is ordered newest first (order assertion shown failing on the old order).\n- [x] The order survives a relaunch (UI test).\n",
   "comments": [],
   "history": [
    {
     "status": "Backlog",
     "at": "2026-11-12T07:30:00Z",
     "by": "claude",
     "note": "filed: follow-up from FLD-3"
    },
    {
     "status": "In progress",
     "at": "2026-11-14T02:00:41Z",
     "by": "claude",
     "note": "worker fld-7, branch fld-7-list-order"
    },
    {
     "status": "In review",
     "at": "2026-11-14T04:26:03Z",
     "by": "claude",
     "note": "PR #13 into dev"
    },
    {
     "status": "Done",
     "at": "2026-11-14T04:38:50Z",
     "by": "claude",
     "note": "squash-merged; review PASS, round 1"
    }
   ],
   "updated": "2026-11-14T04:38:50Z",
   "updated_by": "claude",
   "source": {},
   "lead_decided": {
    "at": "2026-11-14T02:20:00Z",
    "question": "Newest first or oldest first in the record list?",
    "choice": "Newest first: the record just added stays in view."
   }
  },
  {
   "id": "FLD-8",
   "app": "FieldApp",
   "title": "Store listing screenshots",
   "stage": "2 Paid",
   "area": "Release",
   "type": "Chore",
   "size": "M",
   "priority": "P3",
   "status": "Backlog",
   "needs_j": false,
   "pr": "",
   "created": "2026-11-05",
   "tags": [
    "card"
   ],
   "body": "\n# Store listing screenshots\n\nWaits for the paid developer program. The screenshot tour already runs in CI.\n\n## Done when\n- [ ] One screenshot set per device size from the tour.\n- [ ] First real upload shows every size accepted.\n",
   "comments": [],
   "history": [
    {
     "status": "Backlog",
     "at": "2026-11-05T12:00:00Z",
     "by": "claude",
     "note": "filed: split from the release checklist"
    }
   ],
   "updated": "2026-11-05T12:00:00Z",
   "updated_by": "claude",
   "source": {}
  }
 ]
};
