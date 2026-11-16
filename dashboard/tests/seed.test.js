// The example seed (seed/fld_seed.js, invented cards) through the page's counting rules.
// These are the numbers RESTORE.md tells you to expect on a page restored with the example data.
//   node --test dashboard/tests/seed.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
globalThis.window = globalThis;
require("../site/logic.js");
require(path.join("..", "seed", "fld_seed.js"));
require(path.join("..", "seed", "mirror.js"));
const L = globalThis.RoadmapLogic;
const SEED = globalThis.FLD_SEED;
const rows = SEED.cards.map(L.rowFromDoc);
const docOf = (id) => SEED.cards.find((c) => c.id === id);

test("the seed loads under the names app.js asks for", () => {
  assert.equal(L.DB_APPS.FieldApp.collection.toUpperCase() + "_SEED", "FLD_SEED");
  assert.equal(SEED.cards.length, 8);
  assert.deepEqual(globalThis.ROADMAP_MIRROR.cards, []);
});

test("the FieldApp tile: phase 1 Free build, 2 of 5 built, 40%", () => {
  assert.deepEqual(L.summarize("FieldApp", rows), {
    app: "FieldApp", phase: "1 Free build", built: 2, total: 5, phasePre: true, headLabel: "Phase 1 Free build",
    headBuilt: 2, headTotal: 5, headPct: 40, pct: 40, license: 1, review: 1, progress: 1, release: 2, needsYou: 1,
  });
});

test("one open question, shown with the first paragraph of the card's notes", () => {
  const phases = { FieldApp: L.summarize("FieldApp", rows).phase };
  const needs = L.sortNeeds(rows, phases);
  assert.deepEqual(needs.map((c) => c.id), ["FLD-6"]);
  assert.deepEqual(L.openAsks(needs, docOf).map((c) => c.id), ["FLD-6"]);
  assert.match(L.firstNote(docOf("FLD-6").body, 600), /^Question for J .*Recommendation: A/);
});

test("an answer from J takes the card out of the open count until the lead acts", () => {
  const answered = { ...docOf("FLD-6"), comments: [{ at: "2026-11-16T15:00:00Z", by: "J", text: "A" }] };
  const needs = L.sortNeeds(rows, { FieldApp: "1 Free build" });
  assert.deepEqual(L.openAsks(needs, () => answered), []);
});

test("one choice under Decided for you", () => {
  assert.deepEqual(L.leadDecisions(SEED.cards).map((d) => [d.id, d.choice]),
    [["FLD-7", "Newest first: the record just added stays in view."]]);
});

test("in flight: the review and the running card, newest change first", () => {
  const now = Date.parse("2026-11-16T18:00:00Z");
  const flight = L.inFlight(SEED.cards.map(L.flightItemFromDoc), now);
  assert.deepEqual(flight.map((c) => [c.id, c.status, c.quiet]), [["FLD-5", "In progress", false], ["FLD-4", "In review", false]]);
});

test("left before the license: 4 of 7 built, the moving cards first", () => {
  const left = L.preLicenseLeft(rows);
  assert.deepEqual([left.total, left.built, left.left.map((c) => c.id)], [7, 4, ["FLD-4", "FLD-5", "FLD-6"]]);
});

test("since a check-in on 2026-11-16 12:00 UTC: one to review, one started, one queued", () => {
  const ch = L.changesSince(SEED.cards, "2026-11-16T12:00:00Z");
  assert.deepEqual(Object.fromEntries(Object.entries(ch).map(([k, v]) => [k, v.map((c) => c.id)])),
    { built: [], released: [], review: ["FLD-4"], started: ["FLD-5"], queued: ["FLD-6"], back: [], filed: [], note: [] });
});
