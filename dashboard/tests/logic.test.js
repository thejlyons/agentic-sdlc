// Live version as of 2026-11-16, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
// node --test ~/.claude/lead/dashboard/tests/
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
globalThis.window = globalThis;
require("../site/logic.js");
const L = globalThis.RoadmapLogic;
const OUT = path.join(__dirname, "..", "out");
const BACKUP = path.join(__dirname, "..", "..", "dashboard-backup-2026-11-11", "out");
const loadJs = (file) => {
  const s = fs.readFileSync(file, "utf8");
  return JSON.parse(s.slice(s.indexOf("=") + 1).trim().replace(/;$/, ""));
};

// The AppC tile as the live page showed it from the vault mirror before the move (2026-11-11).
const APC_BEFORE = {
  app: "AppC", phase: "1 Refactor", built: 41, total: 42, phasePre: true, headLabel: "Phase 1 Refactor",
  headBuilt: 41, headTotal: 42, headPct: 98, pct: 98, license: 24, review: 0, progress: 1, release: 19, needsYou: 0,
};

test("AppC is a database app with collection apc", () => {
  assert.deepEqual(L.DB_APPS["AppC"], { collection: "apc", prefix: "APC" });
  assert.equal(L.appOfId("APC-45"), "AppC");
  assert.equal(L.appOfId("FLD-1"), "FieldApp");
});

test("AppC tile numbers are the same from the seed as from the old mirror", { skip: !fs.existsSync(path.join(OUT, "apc_seed.js")) }, () => {
  const seed = loadJs(path.join(OUT, "apc_seed.js"));
  assert.equal(seed.cards.length, 235);
  assert.deepEqual(L.summarize("AppC", seed.cards.map(L.rowFromDoc)), APC_BEFORE);
  const old = loadJs(path.join(BACKUP, "mirror.js"));
  const oldApc = old.cards.filter((c) => c.app === "AppC");
  assert.deepEqual(L.summarize("AppC", oldApc), APC_BEFORE);
  // Row by row: what the page showed from the mirror equals what it shows from the database card.
  const byId = new Map(oldApc.map((c) => [c.id, c]));
  for (const card of seed.cards) {
    const { live, ...row } = L.rowFromDoc(card);
    const was = { ...byId.get(card.id) };
    // The mirror stamps the build day in the commit's own zone; compare the instant.
    if (row.built_at || was.built_at) { row.built_at = new Date(row.built_at).toISOString(); was.built_at = new Date(was.built_at).toISOString(); }
    assert.deepEqual(row, was, card.id);
  }
  const now = loadJs(path.join(OUT, "mirror.js"));
  assert.equal(now.cards.filter((c) => c.app === "AppC").length, 0, "the mirror no longer carries AppC");
});

test("a half-finished import shows the same numbers: database cards plus the seed for the rest", { skip: !fs.existsSync(path.join(OUT, "apc_seed.js")) }, () => {
  const seed = loadJs(path.join(OUT, "apc_seed.js"));
  for (const n of [0, 26, 100, 235]) {
    const inDb = seed.cards.filter((c) => !L.built(c)).concat(seed.cards.filter(L.built)).slice(0, n);
    const rows = L.fillFromSeed(inDb, seed.cards).map(L.rowFromDoc);
    assert.equal(rows.length, 235);
    assert.deepEqual(L.summarize("AppC", rows), APC_BEFORE, `with ${n} cards in the database`);
  }
});

test("fillFromSeed keeps the database's version of a card", () => {
  const db = [{ id: "APC-1", status: "Done" }];
  const seed = [{ id: "APC-1", status: "Backlog" }, { id: "APC-2", status: "Backlog" }];
  assert.deepEqual(L.fillFromSeed(db, seed), [{ id: "APC-1", status: "Done" }, { id: "APC-2", status: "Backlog" }]);
  assert.deepEqual(L.fillFromSeed(db, null), db);
});

// ---------- part 2: the new views must not change any count ----------

test("every app's tile numbers are what the 2026-11-11 logic.js computes from the same cards", { skip: !fs.existsSync(BACKUP) }, () => {
  const vm = require("node:vm");
  const ctx = { globalThis: {} }; ctx.window = ctx.globalThis;
  vm.runInNewContext(fs.readFileSync(path.join(BACKUP, "..", "site", "logic.js"), "utf8") + "\nthis.OLD = globalThis.RoadmapLogic || window.RoadmapLogic;", ctx);
  const OLD = ctx.OLD || ctx.globalThis.RoadmapLogic;
  assert.ok(OLD && OLD.summarize, "old logic loaded");
  const cards = loadJs(path.join(OUT, "mirror.js")).cards;
  for (const col of ["fld", "stu", "apc"]) cards.push(...loadJs(path.join(OUT, `${col}_seed.js`)).cards.map(L.rowFromDoc));
  for (const app of L.APPS) {
    const cs = cards.filter((c) => c.app === app);
    assert.ok(cs.length, app);
    assert.deepEqual(JSON.parse(JSON.stringify(L.summarize(app, cs))), JSON.parse(JSON.stringify(OLD.summarize(app, cs))), app);
  }
});

const NOW = Date.parse("2026-11-12T06:00:00Z");
const H = (status, at, by = "lead", note = "", extra = {}) => ({ status, at, by, note, ...extra });

test("ago reads short and treats a slightly future time as just now", () => {
  assert.equal(L.ago("2026-11-12T06:05:00Z", NOW), "just now");
  assert.equal(L.ago("2026-11-12T05:48:00Z", NOW), "12 min");
  assert.equal(L.ago("2026-11-12T01:00:00Z", NOW), "5 h");
  assert.equal(L.ago("2026-11-12T05:00:50Z", NOW), "59 min");
  assert.equal(L.ago("2026-11-12T05:00:20Z", NOW), "1 h", "never 60 min");
  assert.equal(L.ago("2026-11-12T05:00:00Z", NOW), "1 h");
  assert.equal(L.ago("2026-11-09T06:00:00Z", NOW), "3 d");
  assert.equal(L.ago("", NOW), "");
  assert.equal(L.ago("not a date", NOW), "");
});

test("changesSince lists each card once under its last real move after the check-in", () => {
  const since = "2026-11-11T23:20:00Z";
  const docs = [
    { id: "STU-112", app: "StudyApp", title: "a", status: "Done", pr: "78", history: [
      H("Backlog", "2026-11-05T19:56:56-07:00", "vault"), H("In progress", "2026-11-11T23:10:00Z"),
      H("In review", "2026-11-12T03:20:00Z"), H("Done", "2026-11-12T03:45:00Z", "lead", "merged")] },
    { id: "FLD-305", app: "FieldApp", title: "b", status: "In progress", history: [
      H("Backlog", "2026-11-12T03:30:00Z", "lead", "filed"), H("In progress", "2026-11-12T04:00:00Z", "lead", "worker started")] },
    { id: "FLD-306", app: "FieldApp", title: "c", status: "Backlog", history: [H("Backlog", "2026-11-12T03:30:00Z", "lead", "filed")] },
    { id: "FLD-224", app: "FieldApp", title: "d", status: "In progress", history: [
      H("In progress", "2026-11-11T20:40:00Z", "coordinator"), H("In progress", "2026-11-12T02:40:00Z", "claude", "still open")] },
    { id: "FLD-1", app: "FieldApp", title: "old", status: "Done", history: [H("Done", "2026-11-01T00:00:00Z", "vault")] },
    { id: "FLD-2", app: "FieldApp", title: "migrated", status: "Done", history: [H("Done", "2026-11-12T01:00:00Z", "vault", "", { imported: true })] },
    { id: "STU-65", app: "StudyApp", title: "e", status: "In review", history: [
      H("In progress", "2026-11-12T04:00:00Z"), H("In review", "2026-11-12T05:00:00Z"), H("In review", "2026-11-12T05:30:00Z", "lead", "round 2")] },
    { id: "STU-9", app: "StudyApp", title: "back", status: "Backlog", history: [H("In progress", "2026-11-10T00:00:00Z"), H("Backlog", "2026-11-12T05:00:00Z", "lead", "parked")] },
    { id: "STU-10", app: "StudyApp", title: "no history", status: "Backlog" },
  ];
  const ch = L.changesSince(docs, since);
  const ids = (k) => ch[k].map((x) => x.id);
  assert.deepEqual(ids("built"), ["STU-112"]);
  assert.deepEqual(ids("review"), ["STU-65"]);
  assert.equal(ch.review[0].note, "round 2", "the newest entry's note is shown");
  assert.deepEqual(ids("started"), ["FLD-305"]);
  assert.deepEqual(ids("filed"), ["FLD-306"]);
  assert.deepEqual(ids("note"), ["FLD-224"]);
  assert.deepEqual(ids("back"), ["STU-9"]);
  assert.equal(ch.moved, undefined);
  assert.equal(L.CHANGE_KINDS.reduce((n, k) => n + ch[k].length, 0), 6, "old, migrated and history-less cards are left out");
  assert.equal(L.changesSince(docs, "2026-11-12T05:30:00Z").review.length, 0, "an entry at the check-in time itself is not new");
});

test("builtSinceMirror picks vault cards built after the check-in", () => {
  const rows = [{ id: "APD-1", app: "AppD", title: "x", status: "Done", built_at: "2026-11-12T01:00:00Z" },
    { id: "APD-2", app: "AppD", title: "y", status: "Done", built_at: "2026-11-10T01:00:00Z" },
    { id: "APD-3", app: "AppD", title: "z", status: "Backlog", built_at: "" }];
  assert.deepEqual(L.builtSinceMirror(rows, "2026-11-11T23:20:00Z").map((x) => x.id), ["APD-1"]);
});

test("inFlight orders by last change; quiet is 24 h in review, 72 h in progress, and only for cards that should be moving", () => {
  const S1 = "1 Refactor";
  const items = [
    { id: "APC-45", stage: "2 Paid", status: "In progress", needs_j: true, changed: "2026-10-18T23:03:04Z" },   // license stage, waits on J
    { id: "FLD-305", stage: S1, status: "In progress", changed: "2026-11-12T04:00:00Z" },
    { id: "STU-65", stage: S1, status: "In review", changed: "2026-11-12T05:30:00Z" },
    { id: "FLD-9", stage: S1, status: "Backlog", changed: "2026-11-12T05:30:00Z" },
    { id: "FLD-7", stage: S1, status: "In progress", changed: "" },
    { id: "FLD-8", stage: S1, status: "In progress", changed: "2026-11-11T06:00:00Z" },    // 24 h in progress: not yet
    { id: "FLD-6", stage: S1, status: "In progress", changed: "2026-11-09T06:00:00Z" },    // exactly 72 h
    { id: "STU-103", stage: S1, status: "In review", changed: "2026-11-11T06:00:00Z" },    // exactly 24 h in review
    { id: "STU-39", stage: S1, status: "In progress", needs_j: true, changed: "2026-11-01T06:00:00Z" },   // waits on J
    { id: "FLD-35", stage: "3 Release", status: "In progress", changed: "2026-11-01T06:00:00Z" },         // past stage 1
    { id: "APD-39", stage: S1, status: "In progress", mirrored: true, changed: "2026-10-18T18:08:35Z" }, // vault: age is the sync's
  ];
  const f = L.inFlight(items, NOW);
  assert.deepEqual(f.map((x) => x.id), ["STU-65", "FLD-305", "FLD-8", "STU-103", "FLD-6", "FLD-35", "STU-39", "APC-45", "APD-39", "FLD-7"]);
  assert.deepEqual(f.filter((x) => x.quiet).map((x) => x.id), ["STU-103", "FLD-6"]);
  assert.equal(f.find((x) => x.id === "FLD-7").hours, null, "no date is not called quiet");
});

test("appCards fills from the seed unless the import is known to be done", () => {
  const db = [{ id: "APC-45", status: "Done" }], seed = [{ id: "APC-45", status: "In progress" }, { id: "APC-1", status: "Released" }];
  assert.deepEqual(L.appCards(db, seed, true), db, "import recorded done: the database alone");
  assert.deepEqual(L.appCards(db, seed, false).map((c) => c.id), ["APC-45", "APC-1"], "not known done (unfinished, or meta unreadable): filled");
  assert.equal(L.appCards(db, seed, false)[0].status, "Done", "the database's card wins");
  const full = seed.map((c) => ({ ...c, status: "Released" }));
  assert.deepEqual(L.appCards(full, seed, false), full, "filling after a finished import changes nothing");
});

test("meta unreadable: AppC still shows the vault's numbers from 26 database cards plus the seed", { skip: !fs.existsSync(path.join(OUT, "apc_seed.js")) }, () => {
  const seed = loadJs(path.join(OUT, "apc_seed.js")).cards;
  const inDb = seed.filter((c) => !L.built(c));
  assert.equal(inDb.length, 26);
  assert.deepEqual(L.summarize("AppC", L.appCards(inDb, seed, false).map(L.rowFromDoc)), APC_BEFORE);
  assert.notDeepEqual(L.summarize("AppC", L.appCards(inDb, seed, true).map(L.rowFromDoc)), APC_BEFORE, "which is why 'done' must be known, not assumed");
});

test("openAsks: the header counts stage 0 and 1 asks J hasn't answered", () => {
  const needs = [{ id: "STU-39", stage: "1 Free build" }, { id: "FLD-9", stage: "1 Refactor" }, { id: "APC-50", stage: "2 Paid" }, { id: "APD-1", stage: "0 Free build" }];
  const docs = {
    "STU-39": { history: [H("Backlog", "2026-11-01T00:00:00Z", "vault")], comments: [] },
    "FLD-9": { history: [H("In progress", "2026-11-12T02:00:00Z")], comments: [] },
  };
  const docOf = (id) => docs[id];
  assert.deepEqual(L.openAsks(needs, docOf).map((c) => c.id), ["STU-39", "FLD-9", "APD-1"], "license-stage cards are not asks; a vault card with no document still counts");
  docs["STU-39"].comments.push({ at: "2026-11-12T05:00:00Z", by: "J", text: "bought it" });
  assert.deepEqual(L.openAsks(needs, docOf).map((c) => c.id), ["FLD-9", "APD-1"]);
  docs["FLD-9"].comments.push({ at: "2026-11-12T05:10:00Z", by: "J", text: "yes" });
  assert.equal(L.openAsks(needs.slice(0, 3), docOf).length, 0, "a J comment newer than the last history entry drops the count to 0");
  docs["FLD-9"].history.push(H("In progress", "2026-11-12T05:30:00Z", "lead", "one more question"));
  assert.equal(L.openAsks(needs.slice(0, 3), docOf).length, 1, "the lead asking again counts again");
});

test("changesSince: Released is its own group and Backlog to Next reads as queued, not moved back", () => {
  const docs = [
    { id: "A-1", app: "StudyApp", status: "Released", history: [H("Done", "2026-11-10T00:00:00Z"), H("Released", "2026-11-12T01:00:00Z", "lead", "Released with #80")] },
    { id: "A-2", app: "StudyApp", status: "Next", history: [H("Backlog", "2026-11-10T00:00:00Z"), H("Next", "2026-11-12T01:00:00Z")] },
    { id: "A-3", app: "StudyApp", status: "Next", history: [H("In progress", "2026-11-10T00:00:00Z"), H("Next", "2026-11-12T01:00:00Z")] },
    { id: "A-4", app: "StudyApp", status: "Released", history: [H("In review", "2026-11-10T00:00:00Z"), H("Done", "2026-11-12T01:00:00Z"), H("Released", "2026-11-12T02:00:00Z")] },
  ];
  const ch = L.changesSince(docs, "2026-11-11T23:20:00Z");
  assert.deepEqual(ch.built, []);
  assert.deepEqual(ch.released.map((x) => x.id), ["A-4", "A-1"]);
  assert.deepEqual(ch.queued.map((x) => x.id), ["A-2"]);
  assert.deepEqual(ch.back.map((x) => x.id), ["A-3"]);
});

test("sinceWindow: last opened when older than the check-in, else the check-in, else 24 h", () => {
  const ck = "2026-11-12T05:00:00Z";
  assert.deepEqual(L.sinceWindow(ck, "2026-11-11T20:00:00Z", NOW), { since: "2026-11-11T20:00:00Z", kind: "opened" });
  assert.deepEqual(L.sinceWindow(ck, "2026-11-12T05:30:00Z", NOW), { since: ck, kind: "checkin" }, "opened after the report: the report is the start");
  assert.deepEqual(L.sinceWindow(ck, "", NOW), { since: ck, kind: "checkin" });
  assert.deepEqual(L.sinceWindow("", "2026-11-11T20:00:00Z", NOW), { since: "2026-11-11T20:00:00Z", kind: "opened" });
  assert.deepEqual(L.sinceWindow("", "", NOW), { since: "2026-11-11T06:00:00.000Z", kind: "day" });
  assert.equal(L.sinceWindow(ck, "garbage", NOW).kind, "checkin");
  assert.equal(L.sinceWindow(ck, "2026-11-13T00:00:00Z", NOW).kind, "checkin", "a clock that ran ahead is ignored");
});

test("rollVisit: a reload within 30 minutes is the same visit; later it becomes the previous one", () => {
  const iso = (t) => new Date(t).toISOString();
  assert.deepEqual(L.rollVisit(null, NOW), { prev: "", cur: iso(NOW) });
  const first = { prev: "", cur: iso(NOW - 10 * 60000) };
  assert.deepEqual(L.rollVisit(first, NOW), { prev: "", cur: iso(NOW) });
  const old = { prev: "2026-11-10T00:00:00.000Z", cur: iso(NOW - 5 * 3600000) };
  assert.deepEqual(L.rollVisit(old, NOW), { prev: iso(NOW - 5 * 3600000), cur: iso(NOW) });
  assert.deepEqual(L.rollVisit({ prev: "2026-11-10T00:00:00.000Z", cur: iso(NOW - 60000) }, NOW).prev, "2026-11-10T00:00:00.000Z");
  assert.deepEqual(L.rollVisit("junk", NOW), { prev: "", cur: iso(NOW) });
});

test("flightItemFromDoc takes the newest of history, comments and updated as the last change", () => {
  const d = { id: "FLD-224", app: "FieldApp", title: "t", status: "In progress", pr: "261", updated: "2026-11-12T03:16:00Z",
    history: [H("In progress", "2026-11-12T02:40:00Z", "claude", "PR #261")], comments: [{ at: "2026-11-12T04:10:00Z", by: "J", text: "ok" }] };
  const it = L.flightItemFromDoc(d);
  assert.equal(it.changed, "2026-11-12T04:10:00Z");
  assert.equal(it.note, "PR #261");
  assert.equal(it.pr_label, "#261");
  assert.equal(L.flightItemFromDoc({ id: "X-1", app: "StudyApp", status: "In progress" }).changed, "");
  const imported = { id: "APC-45", app: "AppC", status: "In progress", updated: "2026-11-12T04:38:55Z", updated_by: "import from vault",
    history: [H("In progress", "2026-10-18T23:03:04Z", "vault")] };
  assert.equal(L.flightItemFromDoc(imported).changed, "2026-10-18T23:03:04Z", "the import time is not a change");
});

test("preLicenseLeft counts unbuilt stage 0 and 1 cards and puts the moving ones first", () => {
  const cards = [
    { id: "A-1", stage: "0 Free build", status: "Released", priority: "P1" },
    { id: "A-2", stage: "1 Refactor", status: "Backlog", priority: "P2" },
    { id: "A-3", stage: "1 Refactor", status: "Backlog", priority: "P1" },
    { id: "A-4", stage: "1 Refactor", status: "In progress", priority: "P3" },
    { id: "A-5", stage: "1 Refactor", status: "In review", priority: "P3" },
    { id: "A-6", stage: "1 Refactor", status: "Next", priority: "P3" },
    { id: "A-7", stage: "2 Paid", status: "Backlog", priority: "P1" },
    { id: "A-8", stage: "After 1.0", status: "Backlog", priority: "P1" },
    { id: "A-9", stage: "1 Refactor", status: "Done", priority: "P1" },
  ];
  const r = L.preLicenseLeft(cards);
  assert.equal(r.total, 7); assert.equal(r.built, 2);
  assert.deepEqual(r.left.map((c) => c.id), ["A-5", "A-4", "A-6", "A-3", "A-2"]);
  assert.deepEqual(L.preLicenseLeft([{ id: "B-1", stage: "2 Paid", status: "Backlog" }]), { total: 0, built: 0, left: [] });
});

test("preLicenseLeft agrees with the tile for an app whose phase is before the license", { skip: !fs.existsSync(path.join(OUT, "apc_seed.js")) }, () => {
  for (const col of ["fld", "stu", "apc"]) {
    const rows = loadJs(path.join(OUT, `${col}_seed.js`)).cards.map(L.rowFromDoc);
    const s = L.summarize(rows[0].app, rows), r = L.preLicenseLeft(rows);
    if (s.phasePre) assert.equal(r.left.length, s.headTotal - s.headBuilt, rows[0].app);
  }
});

test("answerOf: a note from J newer than the last history entry is an answer; otherwise not", () => {
  const base = { history: [H("In progress", "2026-11-12T02:00:00Z")] };
  assert.equal(L.answerOf({ ...base, comments: [] }), null);
  assert.equal(L.answerOf({ ...base }), null);
  assert.equal(L.answerOf({ ...base, comments: [{ at: "2026-11-12T03:00:00Z", by: "J", text: "yes" }] }).text, "yes");
  assert.equal(L.answerOf({ ...base, comments: [{ at: "2026-11-12T01:00:00Z", by: "J", text: "old" }] }), null, "the lead moved the card after the answer");
  assert.equal(L.answerOf({ ...base, comments: [{ at: "2026-11-12T03:00:00Z", by: "J", text: "yes" }, { at: "2026-11-12T03:30:00Z", by: "lead", text: "which one?" }] }), null, "the lead asked again");
  assert.equal(L.answerOf({ comments: [{ at: "2026-11-12T03:00:00Z", by: "page", text: "yes" }] }).text, "yes");
});

test("leadDecisions lists open lead choices newest first and skips closed or empty ones", () => {
  const docs = [
    { id: "FLD-1", app: "FieldApp", title: "a", lead_decided: { at: "2026-11-13T10:00:00Z", question: "Q1", choice: "C" } },
    { id: "FLD-2", app: "FieldApp", title: "b", lead_decided: { at: "2026-11-13T12:00:00Z", question: "Q2", choice: "A" } },
    { id: "FLD-3", app: "FieldApp", title: "c", lead_decided: { at: "2026-11-13T13:00:00Z", question: "Q3", choice: "B", closed: true } },
    { id: "FLD-4", app: "FieldApp", title: "d", lead_decided: {} },
    { id: "FLD-5", app: "FieldApp", title: "e" },
  ];
  const out = L.leadDecisions(docs);
  assert.deepEqual(out.map((d) => d.id), ["FLD-2", "FLD-1"]);
  assert.equal(out[0].choice, "A");
  assert.equal(out[1].question, "Q1");
});
