// Local preview only: an in-memory stand-in for the artifact runtime's `db` and `user`, so the page
// can be opened from a local folder with no artifact. Nothing is saved; a reload starts empty and the
// page's own import fills it from the seed again. Never publish this file. See RESTORE.md, "Preview".
(function () {
  const store = new Map(), subs = [];
  const snapOf = (col) => ({
    metadata: { fromCache: false },
    docs: [...store.entries()].filter(([p]) => p.startsWith(col + "/"))
      .map(([p, d]) => ({ id: p.slice(col.length + 1), exists: true, data: () => d })),
  });
  const fire = () => subs.forEach(([col, cb]) => setTimeout(() => cb(snapOf(col)), 0));
  const db = {
    collection: (col) => ({ onSnapshot: (cb) => { subs.push([col, cb]); setTimeout(() => cb(snapOf(col)), 0); } }),
    doc: (path) => ({
      get: async () => ({ exists: store.has(path), data: () => store.get(path) }),
      set: async (d) => { store.set(path, d); fire(); },
      update: async (d) => { store.set(path, { ...store.get(path), ...d }); fire(); },
    }),
  };
  const user = { can: async () => true, isOwner: async () => true, id: async () => "preview" };
  window.claude = { use: async (name) => (name === "db" ? db : name === "user" ? user : null) };
  window.__previewStore = store;
})();
