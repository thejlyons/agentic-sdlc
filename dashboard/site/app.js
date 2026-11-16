// Live version as of 2026-11-16, sanitised by scripts/sync.py; app, repo and machine values come from ~/.claude/lead/config.json.
// studio roadmap page. The apps in L.DB_APPS (FieldApp, StudyApp, AppC) come live from
// this artifact's database, one collection each (fld, stu, apc), where J can change a card; the others come
// from mirror.js, a read-only snapshot of the vault rebuilt by sync_vault.py. Every DB app is
// handled the same way, so moving another app is a line in logic.js plus its import.
// Counting rules are in logic.js.
(function () {
  const L = window.RoadmapLogic;
  const MIRROR = window.ROADMAP_MIRROR || { cards: [], apps: [] };
  const COLOR_ORDER = ["AppF", "AppG", "FieldApp", "AppD", "AppC", "AppE", "StudyApp"];
  const appVar = (app) => `var(--s${COLOR_ORDER.indexOf(app) + 1})`;
  const $ = (s) => document.querySelector(s);

  let db = null, user = null, canWrite = false, isOwner = false;
  const DB_APPS = Object.keys(L.DB_APPS);
  const live = Object.fromEntries(DB_APPS.map((a) => [a, new Map()]));      // app -> id -> card document
  const liveState = Object.fromEntries(DB_APPS.map((a) => [a, "loading"])); // loading | slow | cached | live | offline | error
  const importing = new Set(), importChecked = new Set();
  // meta/<collection>_import says an app's move from the vault finished. Until it does, the cards the
  // database doesn't hold yet are shown from the app's seed file, so its numbers never dip mid-move.
  let meta = new Map(), metaState = "loading";                              // loading | ok | error
  const seeds = {}, seedFailed = new Set(), seedLoading = new Set();
  let showLater = false;

  // ---------- helpers ----------
  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "style") el.style.cssText = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : String(kid));
    return el;
  }
  const svgNS = "http://www.w3.org/2000/svg";
  function s(tag, attrs) {
    const el = document.createElementNS(svgNS, tag);
    let style = "";
    for (const [k, v] of Object.entries(attrs || {})) {
      // CSS variables don't resolve in SVG presentation attributes: send colors through style.
      if ((k === "fill" || k === "stroke") && String(v).includes("var(")) style += `${k}:${v};`;
      else el.setAttribute(k, v);
    }
    if (style) el.setAttribute("style", style);
    return el;
  }
  const plural = (n, one, many) => `${n} ${n === 1 ? one : many || one + "s"}`;
  const dayKey = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const fmtDay = (d) => d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  function rel(iso) {
    if (!iso) return "";
    const t = new Date(iso), m = (Date.now() - t) / 60000;
    if (isNaN(t)) return "";
    if (m < 1) return "just now";
    if (m < 60) return `${Math.round(m)} min ago`;
    if (m < 60 * 24) return `${Math.round(m / 60)} h ago`;
    return t.toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  }
  function banner(text) { const b = $("#banner"); b.hidden = !text; b.textContent = text || ""; }

  // ---------- data ----------
  // Done only when meta was read and says so. If meta can't be read the app still waits for its
  // seed and fills from it (see needSeeds): counting only what the database holds would be silently low.
  const importDone = (app) => metaState === "ok" && !!(meta.get(L.DB_APPS[app].collection + "_import") || {}).done;
  const appReady = (app) => metaState !== "loading" && (importDone(app) || !!seeds[app] || seedFailed.has(app));
  function appDocs(app) {
    if (!appReady(app)) return [];
    const docs = [...live[app].values()].filter((d) => d && d.id);
    return L.appCards(docs, seeds[app] ? seeds[app].cards : [], importDone(app));
  }
  function needSeeds() {
    for (const app of DB_APPS) {
      if (importDone(app) || seeds[app] || seedFailed.has(app) || seedLoading.has(app)) continue;
      seedLoading.add(app);
      loadSeed(L.DB_APPS[app].collection).then((seed) => { seeds[app] = seed; }, () => { seedFailed.add(app); })
        .then(() => { seedLoading.delete(app); render(); });
    }
  }
  function liveRows(app) {
    const apps = app ? [app] : DB_APPS;
    return apps.flatMap((a) => appDocs(a).map(L.rowFromDoc));
  }
  function allCards() {
    return MIRROR.cards.filter((c) => !L.LIVE_APPS.has(c.app)).concat(liveRows());
  }
  const isLive = (app) => L.LIVE_APPS.has(app);
  const docOf = (id) => { const a = L.appOfId(id); return a ? live[a].get(id) : undefined; };
  function updatedAt(app) {
    let m = "";
    for (const d of live[app].values()) if (d.updated && d.updated > m) m = d.updated;
    return m;
  }
  const mirroredApps = () => L.APPS.filter((a) => !isLive(a));

  // ---------- render ----------
  let raf = 0;
  function render() { cancelAnimationFrame(raf); raf = requestAnimationFrame(renderNow); }
  function renderNow() {
    const cards = allCards();
    const byApp = Object.fromEntries(L.APPS.map((a) => [a, cards.filter((c) => c.app === a)]));
    const sums = Object.fromEntries(L.APPS.map((a) => [a, L.summarize(a, byApp[a])]));
    const phases = Object.fromEntries(L.APPS.map((a) => [a, sums[a].phase]));
    const now = Date.now();
    const needs = L.sortNeeds(cards, phases);
    const flight = flightItems(now);
    renderHeader(needs, flight, now);
    renderNeeds(needs);
    renderDecided();
    renderSince(now);
    renderFlight(flight, now);
    renderLeft(byApp);
    renderTiles(sums);
    renderBuilt(cards);
    renderMix(byApp);
    renderLiveList();
  }

  const realDocs = () => DB_APPS.flatMap((a) => [...live[a].values()].filter((d) => d && d.id));
  const mirrorRows = () => MIRROR.cards.filter((c) => !isLive(c.app));
  const checkinAt = () => { const c = meta.get("lead_checkin"); return c && L.ms(c.at) ? c.at : ""; };
  const agoText = (iso, now) => { const a = L.ago(iso, now); return a === "just now" || !a ? a : a + " ago"; };
  const anyLoading = () => DB_APPS.some((a) => liveState[a] === "loading" || liveState[a] === "slow" || (db && !appReady(a)));

  // Apps whose cards aren't all on the page yet, and why.
  const loadingApps = () => DB_APPS.filter((a) => db && (liveState[a] === "loading" || liveState[a] === "slow" || !appReady(a)));
  const missingApps = () => DB_APPS.filter((a) => liveState[a] === "offline" || liveState[a] === "error");
  const unsureApps = () => DB_APPS.filter((a) => appReady(a) && !importDone(a) && seedFailed.has(a) && !missingApps().includes(a));
  const list = (xs) => xs.length < 3 ? xs.join(" and ") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1];

  function renderHeader(needs, flight, now) {
    // Questions J has already answered (and the lead hasn't picked up yet) don't count as waiting.
    const asks = L.openAsks(needs, docOf).length;
    const ck = checkinAt();
    const loading = loadingApps(), missing = missingApps(), unsure = unsureApps();
    const firstLoad = loading.length === DB_APPS.length && !loading.some((a) => liveState[a] === "slow");
    $("#takeaway").textContent = firstLoad ? "Loading the cards…" : [
      // With an app still loading, "nothing" isn't known yet, so it isn't claimed.
      asks ? `${plural(asks, "card needs", "cards need")} you` : loading.length || missing.length ? null : "Nothing needs you",
      `${flight.length} in flight`,
      ck ? `lead checked in ${agoText(ck, now)}` : null,
    ].filter(Boolean).join(" · ");
    // What is not on the page is said at the top, in words, not only in the details at the bottom.
    const gaps = [
      !firstLoad && loading.length ? `Still loading ${list(loading)}; the lists and counts on this page leave ${loading.length === 1 ? "it" : "them"} out until then.` : null,
      missing.length ? `${list(missing)} can't be read from the database in this view, so ${missing.length === 1 ? "its" : "their"} cards are missing from every list.` : null,
      unsure.length ? `${list(unsure)}: the move into the database couldn't be confirmed, so some cards may be missing.` : null,
    ].filter(Boolean).join(" ");
    const g = $("#gaps"); g.hidden = !gaps; g.textContent = gaps;
    const livePart = DB_APPS.map((a) => {
      const st = liveState[a], u = updatedAt(a);
      return st === "live" || st === "cached"
        ? `${a}: ${live[a].size} cards live from this page's database${u ? ", last change " + rel(u) : ""}.`
        : st === "offline" ? `${a}: the database isn't available in this view.`
        : st === "error" ? `${a}: the database couldn't be read.` : `${a}: loading from the database…`;
    }).join(" ");
    $("#sources").textContent = `${mirroredApps().join(", ")}: the vault at commit ${MIRROR.vault_commit || "?"}, synced ${rel(MIRROR.synced_at) || "never"}. ${livePart}`;
  }

  // ---------- needs you ----------
  // Each open question in full, with an answer box that saves a note on the card. The list is only
  // rebuilt when what it shows changes, so a snapshot arriving mid-sentence doesn't eat the typing.
  const drafts = new Map();
  let asksSig = null;
  const grow = (ta) => { ta.style.height = "auto"; ta.style.height = Math.min(180, Math.max(40, ta.scrollHeight + 2)) + "px"; };
  function renderNeeds(needs) {
    const asks = needs.filter((c) => L.preLicense(c.stage)), rest = needs.filter((c) => !L.preLicense(c.stage));
    const open = L.openAsks(needs, docOf).length;   // the same number as the header: answered ones stay listed but don't count
    $("#needs-count").textContent = open ? String(open) : asks.length ? "answered" : "";
    // Open questions lead the page. With none open, the page starts at the app tiles and this
    // section (answered cards the lead hasn't picked up yet, later-stage asks) sits below In flight.
    // "Decided for you" always sits right above the tiles, so open questions go just before it.
    const sec = $("#needs"), top = $("#decided"), low = $("#flight");
    if (open) { if (sec.nextElementSibling !== top) top.before(sec); }
    else if (low.nextElementSibling !== sec) low.after(sec);
    sec.querySelector("h2").textContent = open ? "Needs you" : asks.length ? "Answered, waiting to be picked up" : "Needs you";
    const view = asks.map((c) => {
      const doc = docOf(c.id), ans = doc ? L.answerOf(doc) : null;
      return { c, doc, ans, q: doc ? L.firstNote(doc.body, 600) : c.note, editable: !!(doc && db && canWrite) };
    }).sort((a, b) => (a.ans ? 1 : 0) - (b.ans ? 1 : 0));
    const sig = JSON.stringify([anyLoading(), view.map((v) => [v.c.id, v.c.title, v.q, v.ans, v.editable])]);
    if (sig !== asksSig) {
      asksSig = sig;
      const focused = document.activeElement && document.activeElement.id;
      $("#asks").replaceChildren(...(view.length ? view.map(askItem)
        : [h("li", { class: "calm" }, anyLoading() ? "Loading…" : "Nothing needs you right now.")]));
      const again = focused && focused.startsWith("a-") && document.getElementById(focused);
      if (again) again.focus();
    }
    $("#needs-fold").hidden = !rest.length;
    if (rest.length) {
      const toggle = h("li", {}, h("button", { class: "row more", type: "button", "aria-expanded": String(showLater), onclick: () => { showLater = !showLater; render(); } },
        showLater ? "Hide them" : `${rest.length} more wait on the developer license or come after 1.0`));
      $("#needs-list").replaceChildren(toggle, ...(showLater ? rest.map((c) => cardRow(c, (x) => x.thisPhase ? h("span", { class: "pill" }, "this phase") : null)) : []));
    }
  }

  // ---------- decided for you ----------
  // Small choices the lead made on J's behalf; they sit right above the app tiles (below any open
  // questions) until J has seen them, each with a box to ask for a change.
  let decidedSig = null;
  function renderDecided() {
    const sec = $("#decided");
    const items = L.leadDecisions(realDocs());
    sec.hidden = !items.length;
    const top = $("#apps");
    if (sec.nextElementSibling !== top) top.before(sec);
    $("#decided-count").textContent = items.length ? String(items.length) : "";
    const view = items.map((d) => {
      const doc = docOf(d.id), ans = doc ? L.answerOf(doc) : null;
      const c = { id: d.id, app: d.app, title: d.title, priority: "" };
      return { c, ans, editable: !!(doc && db && canWrite), d };
    });
    const sig = JSON.stringify(view.map((v) => [v.d, v.ans, v.editable]));
    if (sig === decidedSig) return;
    decidedSig = sig;
    const focused = document.activeElement && document.activeElement.id;
    $("#decided-list").replaceChildren(...view.map(({ c, ans, editable, d }) => {
      const item = askItem({ c, ans, q: d.question, editable, revise: true });
      const went = h("p", { class: "went" }, h("b", {}, `I went with${d.at ? ", " + agoText(d.at, Date.now()) : ""}: `), d.choice);
      const q = item.querySelector(".q"), title = item.querySelector("h3");
      (q || title).after(went);
      if (editable) {
        // One tap accepts the choice and takes it off the page; a reply below asks for a change instead.
        const msg = h("div", { class: "status-line", role: "status" });
        const ok = h("button", { class: "btn", type: "button", onclick: async () => {
          const cur = docOf(c.id);
          if (!cur || !cur.lead_decided) return;
          ok.disabled = true; msg.textContent = "Saving…";
          try {
            await write(c.id, { lead_decided: { ...cur.lead_decided, closed: true, accepted: true,
              closed_at: new Date().toISOString(), closed_by: isOwner ? "J" : "page" } });
            decidedSig = null; render();
          } catch (err) {
            msg.textContent = "Couldn't save (" + ((err && err.code) || "error") + "). Try again.";
            ok.disabled = false;
          }
        } }, "Looks good");
        went.after(h("div", { class: "accept" }, ok, h("span", { class: "note" }, "or reply below to change it")), msg);
      }
      return item;
    }));
    const again = focused && focused.startsWith("a-") && document.getElementById(focused);
    if (again) again.focus();
  }

  function askItem({ c, ans, q, editable, revise }) {
    const kids = [
      h("div", { class: "ask-top" },
        h("span", { class: "id" }, h("span", { class: "appdot", style: `background:${appVar(c.app)}` }), c.id),
        h("span", {}, [c.app, c.priority].filter(Boolean).join(" · ")),
        h("button", { class: "link", type: "button", onclick: () => openCard(c.id) }, "Open card")),
      h("h3", {}, c.title),
      q ? h("p", { class: "q" }, q) : null,
      ans ? h("p", { class: "yours" }, h("b", {}, `You, ${agoText(ans.at, Date.now())}: `), ans.text) : null,
    ];
    if (editable) {
      const msg = h("div", { class: "status-line", role: "status" });
      const ta = h("textarea", { id: "a-" + c.id, rows: "1", placeholder: ans ? "Add to your answer" : revise ? "OK, or what you'd like instead" : "Your answer", "aria-label": `Answer ${c.id}` });
      ta.value = drafts.get(c.id) || "";
      const send = h("button", { class: "btn", type: "submit", disabled: !ta.value.trim() }, "Send");
      ta.addEventListener("input", () => { drafts.set(c.id, ta.value); grow(ta); send.disabled = !ta.value.trim(); });
      kids.push(h("form", { class: "answer", onsubmit: async (e) => {
        e.preventDefault();
        const text = ta.value.trim(), cur = docOf(c.id);
        if (!text || !cur) return;
        send.disabled = true; msg.textContent = "Saving…";
        try {
          await write(c.id, { comments: [...(cur.comments || []), { at: new Date().toISOString(), by: isOwner ? "J" : "page", text }] });
          drafts.delete(c.id); asksSig = null; render();
        } catch (err) {
          msg.textContent = "Couldn't save (" + ((err && err.code) || "error") + "). Your answer is still in the box.";
          send.disabled = false;
        }
      } }, ta, send), msg);
      if (ta.value) requestAnimationFrame(() => grow(ta));
    } else if (!isLive(c.app)) {
      kids.push(h("p", { class: "note", style: "margin:8px 0 0" }, "This card is in the vault. Answer it in Obsidian."));
    }
    return h("li", { class: "ask" + (ans ? " answered" : "") }, kids);
  }

  // ---------- since the last check-in ----------
  // When this device last had the page open (a convenience kept in this browser only; the page
  // works the same without it and falls back to the lead's check-in).
  let lastOpened = "";
  try {
    const KEY = "roadmap.visit";
    const read = () => { try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; } };
    const roll = () => { const v = L.rollVisit(read(), Date.now()); lastOpened = v.prev; localStorage.setItem(KEY, JSON.stringify(v)); };
    roll();
    const seen = () => { try { document.hidden ? localStorage.setItem(KEY, JSON.stringify({ prev: lastOpened, cur: new Date().toISOString() })) : (roll(), render()); } catch (e) {} };
    document.addEventListener("visibilitychange", seen);
    window.addEventListener("pagehide", () => { try { localStorage.setItem(KEY, JSON.stringify({ prev: lastOpened, cur: new Date().toISOString() })); } catch (e) {} });
  } catch (e) { lastOpened = ""; }

  let sinceDay = false;
  const openGroups = new Set();
  const GROUPS = [["built", "Built", true], ["released", "Released", false], ["review", "Went to review", true], ["started", "Started", true],
    ["queued", "Queued next", true], ["back", "Moved back", true], ["filed", "New cards", false], ["note", "Notes added", false]];
  const WINDOW = {
    opened: { title: "Since you last looked", back: "Since you last looked", empty: "Nothing has changed since you last looked." },
    checkin: { title: "Since the last check-in", back: "Since check-in", empty: "Nothing has changed since the lead's last report." },
    day: { title: "Last 24 hours", back: "", empty: "Nothing changed in the last 24 hours." },
  };
  function renderSince(now) {
    const auto = L.sinceWindow(checkinAt(), lastOpened, now);
    const win = sinceDay ? L.sinceWindow("", "", now) : auto;
    const day = win.kind === "day", since = win.since;
    $("#since-title").textContent = WINDOW[win.kind].title;
    $("#since-count").textContent = day ? "" : agoText(since, now);
    const tog = $("#since-toggle");
    tog.hidden = auto.kind === "day"; tog.textContent = sinceDay ? WINDOW[auto.kind].back : "Last 24 hours";
    const ch = L.changesSince(realDocs(), since);
    ch.built = ch.built.concat(L.builtSinceMirror(mirrorRows(), since)).sort((a, b) => L.ms(b.at) - L.ms(a.at));
    const out = [];
    for (const [key, label, open] of GROUPS) {
      const items = ch[key];
      if (!items.length) continue;
      const shown = open || openGroups.has(key);
      if (open) out.push(h("li", { class: "g" }, h("div", { class: "group" }, label, h("span", { class: "n" }, items.length))));
      else out.push(h("li", {}, h("button", { class: "row more", type: "button", "aria-expanded": String(shown),
        onclick: () => { openGroups.has(key) ? openGroups.delete(key) : openGroups.add(key); render(); } },
        shown ? `Hide ${label.toLowerCase()}` : `${label} · ${items.length}`)));
      if (shown) for (const it of items) out.push(changeRow(it, now));
    }
    $("#since-list").replaceChildren(...(out.length ? out : [h("li", { class: "empty" },
      anyLoading() ? "Loading…" : WINDOW[win.kind].empty)]));
  }
  $("#since-toggle").addEventListener("click", () => { sinceDay = !sinceDay; render(); });

  function changeRow(it, now) {
    return h("li", {}, h("div", { class: "row", role: "button", tabindex: "0",
      onclick: () => openCard(it.id), onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openCard(it.id); } } },
      h("span", { class: "id" }, h("span", { class: "appdot", style: `background:${appVar(it.app)}` }), it.id),
      h("span", { class: "t" }, it.title),
      h("span", { class: "side" }, L.ago(it.at, now)),
      it.note ? h("span", { class: "said" }, it.note) : null));
  }

  // ---------- in flight ----------
  function flightItems(now) {
    const fromMirror = mirrorRows().map((c) => ({ id: c.id, app: c.app, title: c.title, status: c.status, stage: c.stage,
      needs_j: c.needs_j === true, mirrored: true, changed: c.status_at || "", note: c.note || "", by: "vault", pr_label: c.pr_label, pr_url: c.pr_url }));
    return L.inFlight(realDocs().map(L.flightItemFromDoc).concat(fromMirror), now);
  }
  function renderFlight(items, now) {
    const quiet = items.filter((c) => c.quiet).length;
    $("#flight-count").textContent = items.length ? `${items.length}${quiet ? ` · ${quiet} quiet` : ""}` : "";
    $("#flight-list").replaceChildren(...(items.length ? items.map((c) => h("li", {}, h("div", { class: "row", role: "button", tabindex: "0",
      onclick: () => openCard(c.id), onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openCard(c.id); } } },
      h("span", { class: "id" }, h("span", { class: "appdot", style: `background:${appVar(c.app)}` }), c.id),
      h("span", { class: "t" }, c.title),
      h("span", { class: "side" }, prSide(c)),
      h("span", { class: "meta" }, `${c.app} · ${c.status} · `,
        c.mirrored ? `in the vault as of ${rel(MIRROR.synced_at) || "the last sync"}`
          : c.quiet ? h("span", { class: "pill" }, `quiet ${L.ago(c.changed, now)}`)
          : c.changed ? `${c.needs_j ? "waiting on you · " : ""}changed ${agoText(c.changed, now)}` : "no date"),
      c.note ? h("span", { class: "said" }, c.note) : null)))
      : [h("li", { class: "empty" }, anyLoading() ? "Loading…" : "Nothing is in progress or in review.")]));
  }

  // ---------- left before the license ----------
  const openLeft = new Set();
  function renderLeft(byApp) {
    const out = [], complete = [];
    let total = 0;
    for (const app of [...L.APPS.filter(isLive), ...L.APPS.filter((x) => !isLive(x))]) {
      if (isLive(app) && (!appReady(app) || !byApp[app].length)) continue;
      const r = L.preLicenseLeft(byApp[app]);
      if (!r.left.length) { if (r.total) complete.push(app); continue; }
      total += r.left.length;
      const open = openLeft.has(app), show = open ? r.left : r.left.slice(0, 3);
      out.push(h("li", {}, h("div", { class: "app-row", style: `--app:${appVar(app)}` },
        h("span", { class: "name" }, h("span", { class: "appdot", style: `background:${appVar(app)}` }), app),
        h("span", { class: "left" }, h("b", {}, r.left.length), " left"),
        h("div", { class: "bar", role: "img", "aria-label": `${r.built} of ${r.total} built` }, h("i", { style: `width:${r.total ? (r.built * 100) / r.total : 0}%` })))));
      show.forEach((c, i) => out.push(h("li", { class: "sub" + (i === show.length - 1 && r.left.length <= 3 ? " last" : "") }, h("div", { class: "row", role: "button", tabindex: "0",
        onclick: () => openCard(c.id), onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openCard(c.id); } } },
        h("span", { class: "id" }, c.id), h("span", { class: "t" }, c.title),
        h("span", { class: "side" }, c.status === "Backlog" ? c.priority : c.status)))));
      if (r.left.length > 3) out.push(h("li", { class: "sub last" }, h("button", { class: "row more", type: "button", "aria-expanded": String(open),
        onclick: () => { open ? openLeft.delete(app) : openLeft.add(app); render(); } }, open ? "Show the next 3 only" : `Show all ${r.left.length}`)));
    }
    if (complete.length) out.push(h("li", {}, h("div", { class: "complete" }, `Complete: ${complete.join(", ")}`)));
    $("#left-count").textContent = total ? plural(total, "card") : "";
    $("#left-list").replaceChildren(...(out.length ? out : [h("li", { class: "empty" }, "Loading…")]));
  }

  function renderTiles(sums) {
    const box = $("#tiles");
    // Live (database) apps first, so their wide tiles sit side by side.
    const order = [...L.APPS.filter(isLive), ...L.APPS.filter((x) => !isLive(x))];
    box.replaceChildren(...order.map((app) => {
      const r = sums[app], isDb = isLive(app), st = liveState[app];
      const unavailable = isDb && (!appReady(app) || (!live[app].size && st !== "live"));
      const lines = unavailable ? [h("li", { class: "muted" }, st === "loading" || st === "slow" ? "Loading from the database…" : "Database not reachable in this view")] : [
        // Past the license line the headline counts all pre-license work, so say where the phase stands.
        r.phase && !r.phasePre ? h("li", {}, `Phase ${r.phase}: ${r.built}/${r.total} built`) : null,
        h("li", {}, `${r.license} wait on the license`),
        h("li", {}, `${r.review} in review · ${r.progress} in progress`),
        r.release ? h("li", { class: "muted" }, `${r.release} need release`) : null,
        r.needsYou ? h("li", { class: "flag" }, `${plural(r.needsYou, "needs", "need")} you this phase`) : null,
      ];
      const col = isDb ? L.DB_APPS[app].collection : "";
      const from = isDb
        ? `From this page's database (${col}), live${updatedAt(app) ? " · last change " + rel(updatedAt(app)) : ""}`
        : `From the vault, commit ${MIRROR.vault_commit || "?"} · synced ${rel(MIRROR.synced_at)}`;
      // Headline = the vault's per-app block (_scripts/app-progress): the phase while it is before
      // the license, else "Before the license" over stages 0 and 1. See logic.js summarize().
      const pct = r.phase ? r.headPct : 100;
      return h("article", { class: "tile" + (isDb ? " hero" : ""), style: `--app:${appVar(app)}`, id: isDb ? col : null },
        h("header", {}, h("span", { class: "dot" }), h("h3", {}, app), isDb ? h("span", { class: "badge live" }, "Live") : null),
        h("p", { class: "phase" }, unavailable ? " " : r.phase ? r.headLabel : "All stages done"),
        h("div", { class: "big" }, h("span", { class: "pct" }, unavailable ? "—" : `${pct}%`),
          !unavailable && r.phase ? h("span", { class: "frac" }, `${r.headBuilt}/${r.headTotal} built`) : null),
        h("div", { class: "bar", role: "img", "aria-label": `${pct}% built` }, h("i", { style: `width:${unavailable ? 0 : pct}%` })),
        h("ul", { class: "lines" }, lines),
        h("p", { class: "from" }, from));
    }));
  }

  function prSide(c) {
    return c.pr_url ? h("a", { href: c.pr_url, target: "_blank", rel: "noopener", onclick: (e) => e.stopPropagation() }, c.pr_label) : h("span", { class: "meta" }, c.pr_label || "");
  }

  function cardRow(c, side) {
    const meta = [c.app, c.status, c.stage, c.priority].filter(Boolean).join(" · ");
    return h("li", {}, h("div", {
      class: "row", role: "button", tabindex: "0",
      onclick: () => openCard(c.id), onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openCard(c.id); } },
    },
      h("span", { class: "id" }, h("span", { class: "appdot", style: `background:${appVar(c.app)}` }), c.id),
      h("span", { class: "t" }, c.title),
      h("span", { class: "side" }, side ? side(c) : ""),
      h("span", { class: "meta" }, meta)));
  }

  function renderList(sel, rows, side, empty) {
    const ul = $(sel);
    ul.replaceChildren(...(rows.length ? rows.map((c) => cardRow(c, side)) : [h("li", { class: "empty" }, empty)]));
  }

  // ---------- charts ----------
  const tipEl = (box) => box.querySelector(".tip") || box.appendChild(h("div", { class: "tip", hidden: true }));
  function showTip(box, x, y, title, items) {
    const t = tipEl(box);
    t.replaceChildren(h("b", {}, title), ...items.map(([color, name, v]) =>
      h("div", {}, color ? h("i", { style: `background:${color}` }) : null, h("span", {}, name), h("span", {}, v))));
    t.hidden = false;
    const bw = box.clientWidth, tw = t.offsetWidth, th = t.offsetHeight;
    t.style.left = Math.max(4, Math.min(bw - tw - 4, x - tw / 2)) + "px";
    t.style.top = Math.max(4, y - th - 10) + "px";
  }
  const hideTip = (box) => { const t = box.querySelector(".tip"); if (t) t.hidden = true; };
  function textWidth(svg, str) {
    const t = s("text", {}); t.textContent = str; svg.append(t);
    const w = t.getComputedTextLength(); t.remove(); return w;
  }

  function renderBuilt(cards) {
    const box = $("#built-chart");
    box.replaceChildren();
    const W = Math.max(280, box.clientWidth - 24), H = 190;
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const N = W < 520 ? 14 : 28;
    const days = Array.from({ length: N }, (_, i) => { const d = new Date(today); d.setDate(d.getDate() - (N - 1 - i)); return d; });
    const idx = new Map(days.map((d, i) => [dayKey(d), i]));
    const counts = days.map(() => Object.fromEntries(COLOR_ORDER.map((a) => [a, 0])));
    for (const c of cards) {
      if (!c.built_at) continue;
      const i = idx.get(dayKey(new Date(c.built_at)));
      if (i != null && counts[i][c.app] != null) counts[i][c.app]++;
    }
    const totals = counts.map((o) => COLOR_ORDER.reduce((n, a) => n + o[a], 0));
    const max = Math.max(4, ...totals);
    const step = max <= 10 ? 2 : max <= 25 ? 5 : max <= 60 ? 10 : 20;
    const top = Math.ceil(max / step) * step;
    const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", role: "img", "aria-label": `Cards built per day, last ${N} days` });
    box.append(svg);
    const ml = Math.ceil(textWidth(svg, String(top))) + 8, mb = 20, mt = 6, ih = H - mb - mt, iw = W - ml - 2;
    const y = (v) => mt + ih - (v / top) * ih;
    for (let v = 0; v <= top; v += step) {
      svg.append(s("line", { x1: ml, x2: W, y1: y(v), y2: y(v), stroke: "var(--line)", "stroke-width": 1 }));
      const t = s("text", { x: ml - 6, y: y(v) + 4, "text-anchor": "end" }); t.textContent = v; svg.append(t);
    }
    const bw = iw / N, barW = Math.min(28, bw * 0.72);
    days.forEach((d, i) => {
      const x = ml + i * bw + (bw - barW) / 2;
      let acc = 0;
      for (const app of COLOR_ORDER) {
        const n = counts[i][app];
        if (!n) continue;
        const y0 = y(acc), y1 = y(acc + n);
        const hgt = Math.max(1, y0 - y1 - (acc ? 2 : 0));
        svg.append(s("rect", { x, y: y1, width: barW, height: hgt, rx: 2, fill: appVar(app) }));
        acc += n;
      }
      const showLabel = i === 0 || i === N - 1 || (N - 1 - i) % 7 === 0;
      if (showLabel && (i === N - 1 || N - 1 - i >= 3)) {
        const t = s("text", { x: ml + i * bw + bw / 2, y: H - 4, "text-anchor": i === 0 ? "start" : i === N - 1 ? "end" : "middle" });
        if (i === 0) t.setAttribute("x", ml + i * bw);
        if (i === N - 1) t.setAttribute("x", ml + (i + 1) * bw);
        t.textContent = fmtDay(d); svg.append(t);
      }
      const hit = s("rect", { x: ml + i * bw, y: mt, width: bw, height: ih, fill: "transparent" });
      const show = () => {
        const items = COLOR_ORDER.filter((a) => counts[i][a]).map((a) => [appVar(a), a, counts[i][a]]);
        const scale = box.clientWidth / W;
        showTip(box, (ml + i * bw + bw / 2) * scale + 12, y(totals[i]) * scale + 12, `${fmtDay(d)} · ${plural(totals[i], "card")} built`, items.length ? items : [[null, "None", ""]]);
      };
      hit.addEventListener("pointerenter", show); hit.addEventListener("pointerdown", show);
      hit.addEventListener("pointerleave", () => hideTip(box));
      svg.append(hit);
    });
    const total = totals.reduce((a, b) => a + b, 0);
    svg.setAttribute("aria-label", `Cards built per day, last ${N} days: ${total} in all`);
    $("#built-legend").replaceChildren(...COLOR_ORDER.map((a) => h("span", {}, h("i", { style: `background:${appVar(a)}` }), a)),
      h("span", { class: "num" }, `· ${total} in the last ${N} days`));
  }

  const MIX = [
    ["Released", "var(--rel)", (c) => c.status === "Released"],
    ["Done, need release", "var(--done)", (c) => c.status === "Done"],
    ["In review or in progress", "var(--active)", (c) => c.status === "In review" || c.status === "In progress"],
    ["Not started", "var(--todo)", (c) => !["Released", "Done", "In review", "In progress"].includes(c.status)],
  ];
  function renderMix(byApp) {
    const box = $("#mix-chart");
    box.replaceChildren();
    const W = Math.max(280, box.clientWidth - 24), rowH = 30;
    const data = L.APPS.map((app) => {
      const cs = byApp[app].filter((c) => c.stage && c.stage !== "After 1.0");
      return { app, total: cs.length, parts: MIX.map(([name, color, f]) => ({ name, color, n: cs.filter(f).length })) };
    });
    const H = data.length * rowH + 4;
    const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", role: "img", "aria-label": "Cards by status for each app" });
    box.append(svg);
    const narrow = W < 420;
    const labelW = Math.ceil(Math.max(...data.map((d) => textWidth(svg, narrow ? short(d.app) : d.app)))) + 10;
    const endW = Math.ceil(textWidth(svg, "000")) + 8;
    const iw = W - labelW - endW, max = Math.max(1, ...data.map((d) => d.total));
    data.forEach((d, r) => {
      const yy = r * rowH + 6, bh = 16;
      const lab = s("text", { x: 0, y: yy + 12 }); lab.textContent = narrow ? short(d.app) : d.app; svg.append(lab);
      let x = labelW;
      for (const p of d.parts) {
        if (!p.n) continue;
        const w = (p.n / max) * iw, x0 = x;
        const rect = s("rect", { x: x0, y: yy, width: Math.max(1, w - 2), height: bh, rx: 3, fill: p.color });
        const show = () => {
          const scale = box.clientWidth / W;
          showTip(box, (x0 + w / 2) * scale + 12, yy * scale + 12, d.app, [[p.color, p.name, p.n], [null, "1.0 cards", d.total]]);
        };
        rect.addEventListener("pointerenter", show); rect.addEventListener("pointerdown", show);
        rect.addEventListener("pointerleave", () => hideTip(box));
        svg.append(rect);
        x += w;
      }
      const t = s("text", { x: x + 4, y: yy + 12 }); t.textContent = d.total; svg.append(t);
    });
    $("#mix-legend").replaceChildren(...MIX.map(([name, color]) => h("span", {}, h("i", { style: `background:${color}` }), name)));
  }
  const short = (app) => ({ "AppD": "AppD", "AppC": "AppC", AppG: "AppG" }[app] || app);

  // ---------- live card browser (every DB app) ----------
  function renderLiveList() {
    const sel = $("#fld-status"), q = $("#fld-q").value.trim().toLowerCase(), appSel = $("#live-app");
    if (!appSel.options.length) {
      for (const a of [...DB_APPS, ...mirroredApps()]) appSel.append(new Option(a, a));
      appSel.value = DB_APPS[0];
    }
    const app = appSel.value;
    $("#fld-q").placeholder = `Search ${app} cards`;
    const rows = isLive(app) ? liveRows(app) : MIRROR.cards.filter((c) => c.app === app);
    const want = sel.value;
    if (sel.options.length <= 2) {
      for (const st of L.STATUSES) sel.append(new Option(st, st));
    }
    const order = { "In progress": 0, "In review": 1, Next: 2, Backlog: 3, Done: 4, Released: 5 };
    const list = rows.filter((c) => want === "*" ? true : want ? c.status === want : !L.built(c))
      .filter((c) => !q || [c.id, c.title, c.area, c.stage, c.note].join(" ").toLowerCase().includes(q))
      .sort((a, b) => (order[a.status] ?? 9) - (order[b.status] ?? 9) || L.idNum(a.id) - L.idNum(b.id));
    const st = liveState[app];
    const empty = isLive(app) && !live[app].size ? (st === "offline" || st === "error" ? "The database isn't reachable in this view." : "Loading…") : "No cards match.";
    renderList("#fld-list", list, prSide, empty);
  }
  $("#fld-q").addEventListener("input", renderLiveList);
  $("#fld-status").addEventListener("change", renderLiveList);
  $("#live-app").addEventListener("change", renderLiveList);

  // ---------- card detail ----------
  function openCard(id) { if (location.hash !== "#" + id) location.hash = id; else showSheet(id); }
  function closeSheet() {
    $("#scrim").hidden = true; document.body.style.overflow = "";
    if (location.hash) history.replaceState(null, "", location.pathname + location.search);
  }
  $("#scrim").addEventListener("click", (e) => { if (e.target.id === "scrim") closeSheet(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("#scrim").hidden) closeSheet(); });
  window.addEventListener("hashchange", fromHash);
  function fromHash() {
    const id = location.hash.slice(1);
    if (/^[A-Z]+-\d+$/.test(id)) return showSheet(id);
    if (!$("#scrim").hidden) { $("#scrim").hidden = true; document.body.style.overflow = ""; }
    const el = id && document.getElementById(id);
    if (el) el.scrollIntoView();
  }

  function markdown(body) {
    const box = h("div", { class: "md" });
    if (window.marked && window.DOMPurify) {
      box.innerHTML = window.DOMPurify.sanitize(window.marked.parse(String(body || ""), { gfm: true, breaks: false }));
      box.querySelectorAll("a[href]").forEach((a) => { a.target = "_blank"; a.rel = "noopener"; });
    } else {
      box.append(h("pre", { style: "white-space:pre-wrap" }, String(body || "")));
    }
    return box;
  }

  let writing = Promise.resolve();
  function write(id, data) {
    const by = isOwner ? "J" : "page";
    const col = L.DB_APPS[L.appOfId(id)].collection;
    const job = writing.then(() => db.doc(col + "/" + id).update({ ...data, updated: new Date().toISOString(), updated_by: by }));
    writing = job.catch(() => {});
    return job;
  }

  function showSheet(id) {
    const doc = docOf(id);
    const row = doc ? L.rowFromDoc(doc) : allCards().find((c) => c.id === id);
    const sheet = $("#sheet");
    const app = L.appOfId(id);
    if (!row) {
      if (app && (liveState[app] === "loading" || liveState[app] === "slow")) return; // retried when the data arrives
      sheet.dataset.missing = id;
      sheet.replaceChildren(h("div", { class: "top" }, h("h3", { id: "d-title" }, `${id} isn't on the roadmap`), h("button", { class: "close", "aria-label": "Close", onclick: closeSheet }, "×")));
    } else {
      delete sheet.dataset.missing;
      sheet.replaceChildren(...sheetContent(row, doc));
    }
    $("#scrim").hidden = false; document.body.style.overflow = "hidden";
  }

  function sheetContent(c, doc) {
    const editable = !!(doc && db && canWrite);
    const out = [
      h("div", { class: "top" }, h("h3", { id: "d-title" }, `${c.id}  ${c.title}`),
        h("button", { class: "close", "aria-label": "Close", onclick: closeSheet }, "×")),
      h("div", { class: "facts" },
        h("span", {}, h("span", { class: "appdot", style: `background:${appVar(c.app)}` }), c.app),
        [c.stage, c.status, c.priority, c.size && "size " + c.size, c.area, c.type].filter(Boolean).map((x) => h("span", {}, x)),
        c.pr_url ? h("a", { href: c.pr_url, target: "_blank", rel: "noopener" }, "PR " + c.pr_label) : c.pr ? h("span", {}, "PR " + c.pr) : null,
        c.needs_j ? h("span", { class: "pill" }, "needs you") : null),
    ];
    if (!doc) {
      out.push(h("p", { class: "note" }, isLive(c.app)
        ? "This card is still moving into the database, so it can't be changed here yet."
        : `Read-only mirror of the vault (commit ${MIRROR.vault_commit}). Change this card in Obsidian.`));
      if (c.note) out.push(h("div", { class: "md" }, h("p", {}, c.note)));
      return out;
    }
    if (editable) out.push(editBox(c, doc));
    else out.push(h("p", { class: "note" }, db ? "You can read this card but not change it." : "The database isn't available in this view, so the card can't be changed here."));
    if ((doc.comments || []).length) {
      out.push(h("h3", {}, "Notes and answers"), h("ul", { class: "hist comments" },
        [...doc.comments].reverse().map((n) => h("li", {}, h("time", {}, rel(n.at)), h("b", {}, n.by || ""), " ", n.text))));
    }
    const md = markdown(doc.body);
    const boxes = [...md.querySelectorAll('input[type="checkbox"]')];
    const lines = L.taskLines(doc.body);
    if (editable && boxes.length === lines.length) {
      boxes.forEach((b, i) => {
        b.disabled = false;
        b.addEventListener("change", async () => {
          const cur = docOf(c.id);
          const next = L.toggleTask(cur.body, i, b.checked);
          if (next == null) return;
          boxes.forEach((x) => (x.disabled = true));
          try { await write(c.id, { body: next }); }
          catch (e) { b.checked = !b.checked; banner("Couldn't save the checkbox: " + (e && e.code || "error")); }
          boxes.forEach((x) => (x.disabled = false));
        });
      });
    }
    out.push(h("h3", { style: "margin-top:14px" }, "Card"), md);
    out.push(h("h3", { style: "margin-top:16px" }, "History"), h("ul", { class: "hist" },
      [...(doc.history || [])].reverse().map((e) => h("li", {},
        h("time", {}, e.at ? new Date(e.at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : ""),
        h("b", {}, e.status || ""), e.imported ? " (as migrated from Notion)" : "", e.note ? " · " + e.note : "", e.by ? ` · ${e.by}` : ""))));
    const src = doc.source || {};
    out.push(h("p", { class: "note", style: "margin-top:12px" },
      `Imported from the vault at commit ${src.vault_commit || "?"} (${src.file || "?"}); last change ${rel(doc.updated)} by ${doc.updated_by || "?"}.`));
    return out;
  }

  function editBox(c, doc) {
    const status = h("select", { id: "e-status", "aria-label": "Status" },
      [...new Set([...L.STATUSES, doc.status].filter(Boolean))].map((st) => { const o = new Option(st, st); o.selected = st === doc.status; return o; }));
    const needs = h("input", { type: "checkbox", id: "e-needs", checked: doc.needs_j === true });
    const pr = h("input", { type: "text", id: "e-pr", value: doc.pr || "", placeholder: "PR number", inputmode: "numeric", style: "width:100%" });
    const note = h("textarea", { id: "e-note", placeholder: "Add a note or answer a question on this card" });
    const msg = h("div", { class: "status-line full" });
    const save = h("button", { class: "btn", onclick: async () => {
      const cur = docOf(c.id);
      const data = {};
      const at = new Date().toISOString(), by = isOwner ? "J" : "page";
      if (status.value !== cur.status) {
        data.status = status.value;
        data.history = [...(cur.history || []), { status: status.value, at, by, note: "changed on the dashboard" }];
      }
      if (needs.checked !== (cur.needs_j === true)) data.needs_j = needs.checked;
      if (pr.value.trim() !== String(cur.pr || "")) data.pr = pr.value.trim();
      const text = note.value.trim();
      if (text) data.comments = [...(cur.comments || []), { at, by, text }];
      if (!Object.keys(data).length) { msg.textContent = "Nothing changed."; return; }
      save.disabled = true; msg.textContent = "Saving…";
      try {
        await write(c.id, data);
        msg.textContent = "Saved."; note.value = "";
        showSheet(c.id);
      } catch (e) {
        msg.textContent = "Couldn't save (" + ((e && e.code) || "error") + "). Nothing was changed.";
        save.disabled = false;
      }
    } }, "Save");
    return h("div", { class: "edit" },
      h("label", { for: "e-status" }, "Status"), status,
      h("label", { for: "e-needs" }, "Needs you"), h("div", {}, needs),
      h("label", { for: "e-pr" }, "PR"), pr,
      h("div", { class: "full" }, note),
      h("div", { class: "full" }, save), msg);
  }

  // ---------- database ----------
  async function start() {
    try {
      if (window.claude && window.claude.use) {
        db = await window.claude.use("db");
        user = await window.claude.use("user");
      }
    } catch (e) { db = null; }
    if (!db) { for (const a of DB_APPS) liveState[a] = "offline"; render(); return; }
    try {
      if (user) {
        const w = await user.can("data.write");
        canWrite = w !== false;
        isOwner = !!(await user.isOwner());
      } else canWrite = true;
    } catch (e) { canWrite = true; }
    subscribeMeta();
    for (const app of DB_APPS) subscribe(app);
  }

  function subscribeMeta() {
    const fail = () => { if (metaState !== "ok") { metaState = "error"; needSeeds(); render(); } };
    const slow = setTimeout(fail, 10000);
    db.collection("meta").onSnapshot((snap) => {
      clearTimeout(slow);
      meta = new Map(snap.docs.filter((d) => d.exists).map((d) => [d.id, d.data()]));
      metaState = "ok";
      needSeeds();
      render();
    }, () => { clearTimeout(slow); fail(); });
  }

  function subscribe(app) {
    const col = L.DB_APPS[app].collection;
    const slow = setTimeout(() => { if (liveState[app] === "loading") { liveState[app] = "slow"; render(); } }, 10000);
    db.collection(col).onSnapshot((snap) => {
      live[app] = new Map(snap.docs.filter((d) => d.exists).map((d) => [d.id, d.data()]));
      liveState[app] = snap.metadata.fromCache ? "cached" : "live";
      if (!snap.metadata.fromCache) clearTimeout(slow);
      render();
      const missing = $("#sheet").dataset.missing;
      if (missing && docOf(missing)) showSheet(missing);
      else if (/^#[A-Z]+-\d+$/.test(location.hash) && $("#scrim").hidden) fromHash();
      if (!snap.metadata.fromCache) maybeImport(app);
    }, (err) => { clearTimeout(slow); liveState[app] = "error"; render(); banner(`The ${app} cards couldn't be read (${err && err.code}).`); });
  }

  // Owner's visit, once per DB app: copy that app's vault cards (<collection>_seed.js) into the
  // database, only the ones it doesn't hold yet, then record the run in meta/<collection>_import so
  // it never repeats. A card still exactly as imported (updated_by "import from vault") whose
  // content differs from the seed is rewritten from the seed: that repairs a card a thread wrote
  // by hand through db_write with a slip. Cards anyone changed since are never touched.
  async function maybeImport(app) {
    if (importChecked.has(app) || importing.has(app) || !isOwner || !canWrite) return;
    importChecked.add(app);
    const col = L.DB_APPS[app].collection;
    let meta;
    try { meta = await db.doc(`meta/${col}_import`).get(); } catch (e) { importChecked.delete(app); return; }
    if (meta.exists && meta.data().done) return;
    importing.add(app);
    try {
      const seed = await loadSeed(col);
      const have = live[app];
      const todo = seed.cards.filter((c) => !have.has(c.id));
      const fix = seed.cards.filter((c) => {
        const d = have.get(c.id);
        return d && d.updated_by === "import from vault" && canon(strip(d)) !== canon(strip(c));
      });
      let written = 0;
      for (const card of [...todo, ...fix]) {
        banner(`Moving ${app} cards into the database: ${written} of ${todo.length + fix.length}. Keep this page open.`);
        await withRetry(() => db.doc(`${col}/${card.id}`).set(card));
        written++;
      }
      await withRetry(() => db.doc(`meta/${col}_import`).set({
        done: true, at: new Date().toISOString(), written: todo.length, repaired: fix.map((c) => c.id),
        already: seed.cards.length - todo.length, total: seed.cards.length,
        vault_commit: seed.vault_commit, seed_made_at: seed.made_at,
      }));
      banner(written ? `Moved ${todo.length} ${app} cards into the database${fix.length ? ` and repaired ${fix.length}` : ""} (vault commit ${seed.vault_commit}).` : "");
    } catch (e) {
      banner(`The ${app} import stopped (` + ((e && e.code) || (e && e.message) || "error") + "). It picks up where it left off next time you open the page.");
      importChecked.delete(app);
    } finally { importing.delete(app); }
  }
  // Compare a card with its seed ignoring `updated` (the import time) and key order.
  const strip = (d) => { const { updated, ...rest } = d; return rest; };
  function canon(v) {
    if (Array.isArray(v)) return "[" + v.map(canon).join(",") + "]";
    if (v && typeof v === "object") return "{" + Object.keys(v).sort().map((k) => JSON.stringify(k) + ":" + canon(v[k])).join(",") + "}";
    return JSON.stringify(v);
  }
  async function withRetry(fn) {
    for (let i = 0; ; i++) {
      try { return await fn(); } catch (e) {
        const code = e && e.code;
        if (i >= 5 || !(code === "resource_exhausted" || code === "unavailable")) throw e;
        await new Promise((r) => setTimeout(r, 800 * (i + 1) + Math.random() * 400));
      }
    }
  }
  function loadSeed(col) {
    const key = col.toUpperCase() + "_SEED";
    return new Promise((res, rej) => {
      if (window[key]) return res(window[key]);
      const el = document.createElement("script");
      el.src = `${col}_seed.js`;
      el.onload = () => (window[key] && window[key].cards ? res(window[key]) : rej(new Error("no seed")));
      el.onerror = () => rej(new Error(`couldn't load ${col}_seed.js`));
      document.head.append(el);
    });
  }

  let rz = 0;
  window.addEventListener("resize", () => { clearTimeout(rz); rz = setTimeout(render, 150); });
  setInterval(() => { if (!document.hidden) render(); }, 60000);   // keeps "5 h ago" honest on a page left open
  render();
  start();
  if (location.hash) setTimeout(fromHash, 0);
})();
