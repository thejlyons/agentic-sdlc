// Live version as of 2026-11-16, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
// Pure roadmap logic shared by the page and the node tests (no DOM, no db).
// The counting rules copy the vault's _scripts/summary/view.js and _scripts/waiting-on-j/view.js.
(function (root) {
  const APPS = ["FieldApp", "AppF", "AppG", "AppD", "AppC", "AppE", "StudyApp"];
  // Apps whose cards live in this artifact's database, one collection each (keep in step with
  // sync_vault.py DB_APPS). Every other app is read-only from mirror.js. Moving an app: add it here.
  const DB_APPS = {
    FieldApp: { collection: "fld", prefix: "FLD" },
    StudyApp: { collection: "stu", prefix: "STU" },
    "AppC": { collection: "apc", prefix: "APC" },
  };
  const LIVE_APPS = new Set(Object.keys(DB_APPS));
  const appOfId = (id) => Object.keys(DB_APPS).find((a) => String(id).startsWith(DB_APPS[a].prefix + "-")) || null;
  const REPOS = {
    AppF: "appf", AppG: "appg", FieldApp: "fieldapp",
    "AppD": "appd", "AppC": "appc", AppE: "appe", StudyApp: "studyapp",
  };
  const STATUSES = ["Backlog", "Next", "In progress", "In review", "Done", "Released"];
  const PRIORITY = { P1: 1, P2: 2, P3: 3 };
  const built = (c) => c.status === "Done" || c.status === "Released";
  const preLicense = (st) => /^[01] /.test(st || "");
  const stageSort = (a, b) => (a === "After 1.0") - (b === "After 1.0") || a.localeCompare(b);

  function prLink(app, pr) {
    const s = String(pr == null ? "" : pr).trim();
    if (!s) return { label: "", url: "" };
    let m = s.match(/https:\/\/github\.com\/OWNER\/([\w.-]+)\/pull\/(\d+)/);
    let repo, n;
    if (m) { repo = m[1]; n = m[2]; }
    else if ((m = s.match(/([A-Za-z][\w.-]*)\s?#(\d+)/))) { repo = m[1]; n = m[2]; }
    else if ((m = s.match(/(\d+)/))) { repo = REPOS[app] || ""; n = m[1]; }
    else return { label: s, url: "" };
    if (!repo) return { label: s, url: "" };
    let label = repo === REPOS[app] ? `#${n}` : `${repo}#${n}`;
    if (/\d+\D+\d+/.test(s.replace(/https:\/\/\S+\/pull\//g, ""))) label += " +";
    return { label, url: `https://github.com/OWNER/${repo}/pull/${n}` };
  }

  function firstNote(body, limit = 220) {
    const para = [];
    for (const line of String(body || "").split("\n")) {
      const s = line.trim();
      if (s.startsWith("#")) { if (para.length) break; continue; }
      if (!s) { if (para.length) break; continue; }
      para.push(s);
    }
    let note = para.join(" ").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/\[\[([^\]|]+\|)?([^\]]+)\]\]/g, "$2");
    return note.length <= limit ? note : note.slice(0, limit - 1).trimEnd() + "…";
  }

  // The time a card first became built, from its history; imported (migrated) entries don't count.
  function builtAtFromHistory(history) {
    for (const e of history || []) {
      if (e.status === "Done" || e.status === "Released") return e.imported ? "" : e.at || "";
    }
    return "";
  }

  // A card document from the database -> the row shape the mirror uses.
  function rowFromDoc(d) {
    const pr = prLink(d.app, d.pr);
    return {
      id: d.id, app: d.app, title: d.title || "", stage: d.stage || "", status: d.status || "",
      priority: d.priority || "", size: d.size || "", area: d.area || "", type: d.type || "",
      needs_j: d.needs_j === true, pr: d.pr || "", pr_label: pr.label, pr_url: pr.url,
      created: d.created || "", built_at: built(d) ? builtAtFromHistory(d.history) : "",
      note: built(d) ? "" : firstNote(d.body), live: true,
    };
  }

  // Cards of a DB app while its import from the vault is unfinished: every document the database
  // holds, plus the seed's card for each id it doesn't hold yet, so the counts don't dip mid-import.
  function fillFromSeed(docs, seedCards) {
    const have = new Set(docs.map((d) => d.id));
    return docs.concat((seedCards || []).filter((c) => c && c.id && !have.has(c.id)));
  }

  function phaseOf(cards) {
    const stages = [...new Set(cards.map((c) => c.stage).filter(Boolean))].sort(stageSort);
    return stages.find((st) => cards.some((c) => c.stage === st && !built(c)));
  }

  // Two numbers, as the vault's Dashboard note shows them:
  //  - phase/built/total/pct: the summary tile (_scripts/summary/view.js), the current phase x/y;
  //  - head*: the per-app block (_scripts/app-progress/view.js), the headline J reads in Obsidian:
  //    the current phase while it is before the license (stage 0 or 1), otherwise every stage 0
  //    and 1 card ("Before the license"). An app whose pre-license work is all built shows 100%
  //    there while its summary tile shows the licensed phase at 0%.
  const jsRound = (x) => Math.round(x);
  function summarize(app, cards) {
    const phase = phaseOf(cards);
    const inPhase = cards.filter((c) => c.stage === phase);
    const done = inPhase.filter(built).length;
    const phasePre = !!phase && preLicense(phase);
    const head = phasePre ? inPhase : cards.filter((c) => preLicense(c.stage));
    const headBuilt = head.filter(built).length;
    return {
      app, phase: phase || null, built: done, total: inPhase.length,
      phasePre, headLabel: phasePre ? `Phase ${phase}` : "Before the license",
      headBuilt, headTotal: head.length, headPct: head.length ? jsRound((headBuilt * 100) / head.length) : 0,
      pct: phase ? (inPhase.length ? Math.round((done * 100) / inPhase.length) : 0) : 100,
      license: cards.filter((c) => c.stage && !preLicense(c.stage) && c.stage !== "After 1.0" && !built(c)).length,
      review: cards.filter((c) => c.status === "In review").length,
      progress: cards.filter((c) => c.status === "In progress").length,
      release: cards.filter((c) => c.status === "Done" && String(c.pr || "").trim()).length,
      needsYou: inPhase.filter((c) => c.needs_j === true && !built(c)).length,
    };
  }

  // Lines of the body that are task items ("- [ ]" / "- [x]"), outside code fences, in order.
  function taskLines(body) {
    const out = [];
    let fence = null;
    String(body || "").split("\n").forEach((line, i) => {
      const f = line.match(/^\s*(```|~~~)/);
      if (f) { fence = fence ? (fence === f[1] ? null : fence) : f[1]; return; }
      if (!fence && /^\s*(?:[-*+]|\d+[.)])\s+\[[ xX]\](?:\s|$)/.test(line)) out.push(i);
    });
    return out;
  }

  function toggleTask(body, n, checked) {
    const lines = String(body).split("\n");
    const idx = taskLines(body)[n];
    if (idx == null) return null;
    lines[idx] = lines[idx].replace(/\[[ xX]\]/, checked ? "[x]" : "[ ]");
    return lines.join("\n");
  }

  function sortNeeds(cards, phases) {
    const appRank = (a) => APPS.indexOf(a);
    return cards
      .filter((c) => c.needs_j === true && !built(c))
      .map((c) => ({ ...c, thisPhase: c.stage === phases[c.app] }))
      .sort((a, b) => (b.thisPhase - a.thisPhase) || (appRank(a.app) - appRank(b.app)) ||
        ((PRIORITY[a.priority] || 9) - (PRIORITY[b.priority] || 9)) || idNum(a.id) - idNum(b.id));
  }

  const idNum = (id) => Number(String(id).split("-")[1]) || 0;

  // ---------- the "what changed, what is moving, what is left" views (read-only; no counting rule above depends on them) ----------
  const ms = (iso) => { const t = Date.parse(iso || ""); return isNaN(t) ? 0 : t; };

  // "12 min", "5 h", "3 d": how long ago, for a time that may be a little in the future (the lead
  // writes some times by hand), which reads as "just now".
  function ago(iso, now) {
    const t = ms(iso);
    if (!t) return "";
    const m = (now - t) / 60000;
    if (m < 1) return "just now";
    if (m < 59.5) return `${Math.round(m)} min`;
    if (m < 60 * 36) return `${Math.max(1, Math.round(m / 60))} h`;
    return `${Math.round(m / 1440)} d`;
  }

  // What a DB app's list is built from: the database's cards, plus the seed's card for every id the
  // database lacks unless the import is known to be finished. "Known" matters: when meta can't be
  // read, a loaded seed still fills, because filling after a finished import changes nothing.
  function appCards(docs, seedCards, importKnownDone) {
    return importKnownDone ? docs : fillFromSeed(docs, seedCards);
  }

  // needs_j cards J can act on now (stages 0 and 1) that he hasn't answered yet: the header's count.
  // Not the tile's "need you this phase", which counts needs_j in the app's current phase, answered or not.
  function openAsks(needs, docOf) {
    return needs.filter((c) => {
      if (!preLicense(c.stage)) return false;
      const d = docOf(c.id);
      return !(d && answerOf(d));
    });
  }

  // Which window "what changed" covers. The time J last opened the page on this device wins when it
  // is older than the lead's last check-in (the check-in can be minutes old); then the check-in;
  // then the last 24 hours.
  function sinceWindow(checkinIso, lastOpenedIso, now) {
    const ck = ms(checkinIso), lo = ms(lastOpenedIso);
    if (lo && lo < now && (!ck || lo < ck)) return { since: lastOpenedIso, kind: "opened" };
    if (ck) return { since: checkinIso, kind: "checkin" };
    return { since: new Date(now - 86400000).toISOString(), kind: "day" };
  }
  // Per-device visit memory: `prev` is when the visit before this one was last seen. Opening the
  // page again within VISIT_GAP_MIN of the last sighting is the same visit (a reload keeps `prev`).
  const VISIT_GAP_MIN = 30;
  function rollVisit(stored, now) {
    const s = stored && typeof stored === "object" ? stored : {};
    const cur = ms(s.cur), nowIso = new Date(now).toISOString();
    if (cur && now - cur > VISIT_GAP_MIN * 60000) return { prev: s.cur, cur: nowIso };
    return { prev: ms(s.prev) ? s.prev : "", cur: nowIso };
  }

  // What one history entry did, given the entry before it. Entries can repeat a status (a note
  // without a move), and a card's first entry is its filing unless it was migrated in.
  function entryKind(entry, prev) {
    if (!prev) return entry.imported ? "imported" : entry.status === "Backlog" || entry.status === "Next" ? "filed" : kindOfStatus(entry.status);
    if (prev.status === entry.status) return "note";
    const k = kindOfStatus(entry.status);
    // Backlog or Next: forward from Backlog to Next is "queued", anything else landing there went back.
    return k === "moved" ? (entry.status === "Next" && prev.status === "Backlog" ? "queued" : "back") : k;
  }
  // Released is its own kind: a dev to main release moves every Done card at once, and those were
  // already listed as built when they merged.
  const kindOfStatus = (st) => st === "Done" ? "built" : st === "Released" ? "released" : st === "In review" ? "review"
    : st === "In progress" ? "started" : "moved";

  // Cards whose history has entries after `sinceIso`, each once, under the last real move it made
  // in that window (a card that started, went to review and merged shows as built); a card with
  // only notes in the window is "note". Newest first within a kind.
  const CHANGE_KINDS = ["built", "released", "review", "started", "queued", "back", "filed", "note"];
  function changesSince(docs, sinceIso) {
    const since = ms(sinceIso);
    const out = Object.fromEntries(CHANGE_KINDS.map((k) => [k, []]));
    for (const d of docs) {
      const h = d.history || [];
      let kind = "", last = null, filed = false;
      h.forEach((e, i) => {
        if (ms(e.at) <= since) return;
        const k = entryKind(e, h[i - 1]);
        if (k === "imported") return;
        if (k === "filed") filed = true;
        if (k !== "note" || !kind) kind = k === "note" ? "note" : k;
        last = e;
      });
      if (!last) continue;
      // Filed and then built in the same window is built; filed and still waiting is filed.
      if (filed && (kind === "queued" || kind === "back" || kind === "note")) kind = "filed";
      if (kind === "moved") kind = "back";   // a first entry straight into an unknown status
      out[kind].push({ id: d.id, app: d.app, title: d.title || "", status: d.status || "", at: last.at || "", by: last.by || "",
        note: last.note || "", pr: d.pr || "" });
    }
    for (const k of CHANGE_KINDS) out[k].sort((a, b) => ms(b.at) - ms(a.at) || idNum(a.id) - idNum(b.id));
    return out;
  }

  // Mirrored (vault) rows carry no history, only the day they were first built.
  function builtSinceMirror(rows, sinceIso) {
    const since = ms(sinceIso);
    return rows.filter((c) => c.built_at && ms(c.built_at) > since)
      .map((c) => ({ id: c.id, app: c.app, title: c.title, status: c.status, at: c.built_at, by: "vault", note: "", pr: c.pr || "" }));
  }

  // Cards being worked on, with the time of their last change, most recently changed first.
  // "Quiet" marks a card that should be moving and isn't: In review with no change for a day, In
  // progress for three. Never flagged: a card waiting on J (needs_j), a card past stage 1 (it waits
  // on the license or an outside party), and a vault card, whose age is only as fresh as the last sync.
  const QUIET_HOURS = { "In review": 24, "In progress": 72 };
  function inFlight(items, now) {
    return items.filter((c) => c.status === "In progress" || c.status === "In review")
      .map((c) => {
        const t = ms(c.changed);
        const hours = t ? Math.max(0, (now - t) / 3600000) : null;
        const canStall = !c.mirrored && c.needs_j !== true && preLicense(c.stage);
        return { ...c, hours, quiet: canStall && hours != null && hours >= QUIET_HOURS[c.status] };
      })
      .sort((a, b) => ms(b.changed) - ms(a.changed) || idNum(a.id) - idNum(b.id));
  }
  // A database card as an in-flight item: last change is the newest of its history, comments and `updated`.
  function flightItemFromDoc(d) {
    const h = d.history || [], last = h[h.length - 1] || {};
    // `updated` on a card nobody has touched since its import is the import time, not a change.
    const touched = d.updated_by === "import from vault" ? "" : d.updated;
    const times = [touched, last.at, ...(d.comments || []).map((n) => n.at)].filter((x) => ms(x));
    const changed = times.sort((a, b) => ms(b) - ms(a))[0] || "";
    const pr = prLink(d.app, d.pr);
    return { id: d.id, app: d.app, title: d.title || "", status: d.status || "", stage: d.stage || "", needs_j: d.needs_j === true, changed,
      note: last.note || "", by: last.by || "", pr_label: pr.label, pr_url: pr.url };
  }

  // Pre-license work left for one app: every stage 0 and 1 card that isn't built, the ones being
  // worked on first, then Next, then the backlog by priority.
  const NEXT_RANK = { "In review": 0, "In progress": 1, Next: 2 };
  function preLicenseLeft(cards) {
    const pre = cards.filter((c) => preLicense(c.stage));
    const left = pre.filter((c) => !built(c)).sort((a, b) => (NEXT_RANK[a.status] ?? 3) - (NEXT_RANK[b.status] ?? 3) ||
      (PRIORITY[a.priority] || 9) - (PRIORITY[b.priority] || 9) || idNum(a.id) - idNum(b.id));
    return { total: pre.length, built: pre.length - left.length, left };
  }

  // A needs_j card counts as answered when the newest thing on it is a note from J: newer than
  // every history entry, so the lead hasn't acted on it yet.
  function answerOf(doc) {
    const notes = doc.comments || [];
    const last = notes[notes.length - 1];
    if (!last || !(last.by === "J" || last.by === "page")) return null;
    const h = doc.history || [];
    const lastMove = h.length ? ms(h[h.length - 1].at) : 0;
    return ms(last.at) >= lastMove ? last : null;
  }

  // Small choices the lead made itself after J didn't answer within about 15 minutes (J, 2026-11-13).
  // A card carries `lead_decided: { at, question, choice }`; the lead sets `closed: true` once J has
  // seen it (said OK, or asked for a change and the lead handled it). Newest first.
  function leadDecisions(docs) {
    return docs.filter((d) => d && d.lead_decided && typeof d.lead_decided === "object" && !d.lead_decided.closed
        && (d.lead_decided.choice || d.lead_decided.question))
      .map((d) => ({ id: d.id, app: d.app, title: d.title || "", at: d.lead_decided.at || "",
        question: String(d.lead_decided.question || ""), choice: String(d.lead_decided.choice || "") }))
      .sort((a, b) => ms(b.at) - ms(a.at) || idNum(a.id) - idNum(b.id));
  }

  root.RoadmapLogic = {
    leadDecisions,
    APPS, DB_APPS, LIVE_APPS, appOfId, REPOS, STATUSES, built, preLicense, stageSort, prLink, firstNote,
    builtAtFromHistory, rowFromDoc, fillFromSeed, phaseOf, summarize, taskLines, toggleTask, sortNeeds, idNum,
    ms, ago, entryKind, CHANGE_KINDS, changesSince, builtSinceMirror, QUIET_HOURS, inFlight, flightItemFromDoc,
    preLicenseLeft, answerOf, appCards, openAsks, sinceWindow, rollVisit, VISIT_GAP_MIN,
  };
})(typeof window !== "undefined" ? window : globalThis);
