"""Tests for the restore tools, on the example data only (no network, no private files).

  python3 -m unittest discover -s dashboard/tests -p 'test_*.py'
"""
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DASH = Path(__file__).resolve().parent.parent
REPO = DASH.parent
sys.path.insert(0, str(DASH))
import configure_apps  # noqa: E402
import export_cards  # noqa: E402
import roadmap_card as rc  # noqa: E402
import sync_vault as sv  # noqa: E402

FIELDS = {"id", "app", "title", "stage", "area", "type", "size", "priority", "status", "needs_j", "pr",
          "created", "tags", "body", "comments", "history", "updated", "updated_by", "source"}


def load_js(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    start = text.index("=", text.index("window.")) + 1
    return json.loads(text[start:].strip().rstrip(";"))


def run(fn, argv) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            code = fn(argv)
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
    return code, out.getvalue()


SEED = load_js(DASH / "seed" / "fld_seed.js")


class SeedShape(unittest.TestCase):
    def test_every_card_has_the_document_fields(self):
        self.assertEqual([c["id"] for c in SEED["cards"]], [f"FLD-{n}" for n in range(1, 9)])
        for c in SEED["cards"]:
            self.assertEqual(FIELDS - set(c), set(), c["id"])
            self.assertEqual(c["app"], "FieldApp")
            self.assertIn(c["status"], rc.STATUSES)
            self.assertIsInstance(c["needs_j"], bool)
            self.assertEqual(c["history"][-1]["status"], c["status"], c["id"])
            times = [e["at"] for e in c["history"]]
            self.assertEqual(times, sorted(times), c["id"])
            self.assertIn("## Done when", c["body"])

    def test_every_status_is_shown_and_one_card_asks_and_one_is_decided(self):
        self.assertEqual({c["status"] for c in SEED["cards"]}, set(rc.STATUSES))
        self.assertEqual([c["id"] for c in SEED["cards"] if c["needs_j"]], ["FLD-6"])
        self.assertEqual([c["id"] for c in SEED["cards"] if c.get("lead_decided")], ["FLD-7"])

    def test_the_mirror_is_empty_and_valid(self):
        self.assertEqual(load_js(DASH / "seed" / "mirror.js")["cards"], [])


class CardTool(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_op_appends_one_history_entry_and_keeps_the_rest(self):
        card = next(c for c in SEED["cards"] if c["id"] == "FLD-5")
        f = self.tmp / "card.json"
        f.write_text(json.dumps({"version": 4, "data": card}))
        code, out = run(rc.main, ["op", str(f), "--status", "In review", "--pr", "15", "--note", "PR #15 into dev"])
        self.assertEqual(code, 0)
        op = json.loads(out)
        self.assertEqual((op["op"], op["path"], op["ifVersion"]), ("update", "fld/FLD-5", 4))
        self.assertEqual(op["data"]["history"][:-1], card["history"])
        self.assertEqual(op["data"]["history"][-1]["status"], "In review")
        self.assertEqual(op["data"]["pr"], "15")

    def test_op_without_a_version_is_refused(self):
        f = self.tmp / "card.json"
        f.write_text(json.dumps({"data": SEED["cards"][0]}))
        code, _ = run(rc.main, ["op", str(f), "--status", "Done"])
        self.assertNotEqual(code, 0)

    def test_new_prints_a_set_op_in_the_app_collection(self):
        code, out = run(rc.main, ["new", "--app", "FieldApp", "--id", "FLD-9", "--title", "T", "--stage", "1 Free build",
                                  "--note", "why"])
        self.assertEqual(code, 0)
        op = json.loads(out)
        self.assertEqual((op["op"], op["path"]), ("set", "fld/FLD-9"))
        self.assertNotIn("ifVersion", op)
        self.assertEqual(FIELDS - set(op["data"]), set())

    def test_to_md_round_trips_fields_and_body(self):
        for card in SEED["cards"]:
            fm, _, body = sv.split_card(rc.card_to_md(card))
            self.assertEqual(body, card["body"])
            for k in ("id", "app", "title", "stage", "status", "priority", "size", "pr", "created", "needs_j", "tags"):
                self.assertEqual(fm[k], card[k], f"{card['id']} {k}")


class ExampleVault(unittest.TestCase):
    def test_the_vault_files_are_the_seed_cards(self):
        files = sorted((DASH / "example-vault" / "Roadmaps" / "FieldApp").glob("*.md"))
        self.assertEqual(len(files), 4)
        by_id = {c["id"]: c for c in SEED["cards"]}
        for f in files:
            self.assertEqual(f.read_text(encoding="utf-8"), rc.card_to_md(by_id[f.name.split(" ")[0]]))

    def test_seed_and_import_from_a_vault_that_is_a_git_repo(self):
        if not shutil.which("git"):
            self.skipTest("git not installed")
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        vault = tmp / "vault"
        shutil.copytree(DASH / "example-vault", vault)
        git = ["git", "-C", str(vault), "-c", "user.name=example", "-c", "user.email=example",
               "-c", "commit.gpgsign=false"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "FLD: example cards"], check=True)
        code, out = run(rc.main, ["seed", "--app", "FieldApp", "--vault", str(vault), "--out", str(tmp / "fld_seed.js")])
        self.assertEqual(code, 0, out)
        seed = load_js(tmp / "fld_seed.js")
        self.assertEqual([c["id"] for c in seed["cards"]], ["FLD-3", "FLD-5", "FLD-6", "FLD-8"])
        by_id = {c["id"]: c for c in SEED["cards"]}
        for c in seed["cards"]:
            self.assertEqual(c["body"], by_id[c["id"]]["body"])
            self.assertEqual(c["updated_by"], "import from vault")
            # One commit, so one history entry: the status the file was added with.
            self.assertEqual([e["status"] for e in c["history"]], [c["status"]])
            self.assertEqual(rc.card_to_md(c), rc.card_to_md(by_id[c["id"]]))
        code, out = run(rc.main, ["import", "--app", "FieldApp", "--vault", str(vault), "--out", str(tmp / "batches")])
        self.assertEqual(code, 0, out)
        ops = json.loads((tmp / "batches" / "batch_01.json").read_text())["ops"]
        self.assertEqual([(o["op"], o["path"]) for o in ops],
                         [("set", f"fld/FLD-{n}") for n in (3, 5, 6, 8)])


class Export(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        cards = SEED["cards"]
        # Three shapes a thread might save, with one card twice (the higher version must win).
        (self.tmp / "a.json").write_text(json.dumps(
            {"documents": [{"path": f"fld/{c['id']}", "version": 2, "data": c} for c in cards[:4]]}))
        newer = dict(cards[0], status="Done")
        (self.tmp / "b.json").write_text(json.dumps(
            [{"path": "fld/FLD-1", "version": 1, "data": newer},
             {"path": "meta/lead_checkin", "version": 3, "data": {"at": "2026-11-16T17:00:00Z", "by": "lead"}}]))
        (self.tmp / "c.jsonl").write_text("\n".join(json.dumps(c) for c in cards[4:]) + "\n")
        self.files = [str(self.tmp / n) for n in ("a.json", "b.json", "c.jsonl")]
        self.out = self.tmp / "backup"

    def test_export_writes_json_markdown_and_an_index_and_verifies(self):
        code, out = run(export_cards.main, self.files + ["--out", str(self.out)])
        self.assertEqual(code, 0, out)
        saved = json.loads((self.out / "cards.json").read_text())
        self.assertEqual([c["data"]["id"] for c in saved], [f"FLD-{n}" for n in range(1, 9)])
        self.assertEqual(saved[0]["data"]["status"], "Released")  # version 2 beat version 1
        self.assertEqual(saved[6]["data"]["lead_decided"]["choice"], SEED["cards"][6]["lead_decided"]["choice"])
        self.assertEqual([m["path"] for m in json.loads((self.out / "meta.json").read_text())], ["meta/lead_checkin"])
        self.assertEqual(len(list((self.out / "Roadmaps" / "FieldApp").glob("*.md"))), 8)
        self.assertIn("| FieldApp | 1 | 1 | 1 | 1 | 2 | 2 | 8 |", (self.out / "index.md").read_text())
        code, out = run(export_cards.main, ["--verify", str(self.out)])
        self.assertEqual(code, 0, out)

    def test_verify_catches_a_changed_file(self):
        run(export_cards.main, self.files + ["--out", str(self.out)])
        f = next((self.out / "Roadmaps" / "FieldApp").glob("FLD-3*.md"))
        f.write_text(f.read_text().replace('status: "Done"', 'status: "Backlog"'))
        code, out = run(export_cards.main, ["--verify", str(self.out)])
        self.assertEqual(code, 1)
        self.assertIn("DIFFERS FLD-3: status", out)

    def test_export_refuses_to_write_inside_the_repo(self):
        code, out = run(export_cards.main, self.files + ["--out", str(DASH / "out" / "backup")])
        self.assertEqual(code, 1)
        self.assertFalse((DASH / "out" / "backup").exists())


class ConfigureApps(unittest.TestCase):
    CONFIG = {
        "owner": {"github": "example-owner"},
        "apps": [
            {"name": "Trail Notes", "prefix": "TRL", "repo": "example-owner/trail-notes", "roadmap": "dashboard",
             "collection": "trl"},
            {"name": "Ledger", "prefix": "LDG", "repo": "example-owner/ledger", "roadmap": "vault"},
        ],
    }

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.cfg = self.tmp / "config.json"
        self.cfg.write_text(json.dumps(self.CONFIG))
        self.out = self.tmp / "build"

    def test_dry_run_writes_nothing(self):
        code, out = run(configure_apps.main, ["--config", str(self.cfg), "--out", str(self.out), "--dry-run"])
        self.assertEqual(code, 0, out)
        self.assertIn("would write", out)
        self.assertFalse(self.out.exists())

    def test_the_copy_names_the_configured_apps_and_no_example_app(self):
        code, out = run(configure_apps.main, ["--config", str(self.cfg), "--out", str(self.out)])
        self.assertEqual(code, 0, out)
        logic = (self.out / "site" / "logic.js").read_text()
        self.assertIn('const APPS = ["Trail Notes", "Ledger"];', logic)
        self.assertIn('"Trail Notes": { collection: "trl", prefix: "TRL" },', logic)
        self.assertIn("github.com/example-owner/", logic)
        self.assertIn('const COLOR_ORDER = ["Trail Notes", "Ledger"];', (self.out / "site" / "app.js").read_text())
        for rel in ("site/logic.js", "sync_vault.py"):
            text = (self.out / rel).read_text()
            constants = text[text.index("DB_APPS = {"):text.index("STATUSES" if rel.endswith(".js") else "BUILT = ")]
            for gone in ("FieldApp", "StudyApp", "AppC", "OWNER"):
                self.assertNotIn(gone, constants, rel)
        self.assertNotIn("github.com/OWNER", (self.out / "sync_vault.py").read_text().replace("\\", ""))
        # The configured logic.js still loads and knows the new app.
        if shutil.which("node"):
            js = ("globalThis.window = globalThis; require(process.argv[1]); const L = globalThis.RoadmapLogic;"
                  "console.log(JSON.stringify([L.APPS, L.appOfId('TRL-4'), L.prLink('Ledger', '7').url]))")
            r = subprocess.run(["node", "-e", js, str(self.out / "site" / "logic.js")], capture_output=True, text=True)
            self.assertEqual(json.loads(r.stdout), [["Trail Notes", "Ledger"], "Trail Notes",
                                                    "https://github.com/example-owner/ledger/pull/7"], r.stderr)
        # The configured sync_vault.py still compiles.
        compile((self.out / "sync_vault.py").read_text(), "sync_vault.py", "exec")

    def test_a_missing_constant_fails_and_writes_nothing(self):
        src = self.tmp / "src"
        shutil.copytree(DASH, src, ignore=shutil.ignore_patterns("__pycache__", "out", "example-vault"))
        logic = src / "site" / "logic.js"
        logic.write_text(logic.read_text().replace("const APPS = [", "const ALL_APPS = ["))
        code, out = run(configure_apps.main, ["--config", str(self.cfg), "--src", str(src), "--out", str(self.out)])
        self.assertEqual(code, 1)
        self.assertIn("logic.js APPS", out)
        self.assertFalse(self.out.exists())

    def test_bad_config_and_an_output_folder_inside_the_repo_are_refused(self):
        self.cfg.write_text(json.dumps({"owner": {"github": "example-owner"}, "apps": [
            {"name": "X", "prefix": "X", "roadmap": "dashboard", "collection": "meta"}]}))
        self.assertEqual(run(configure_apps.main, ["--config", str(self.cfg), "--out", str(self.out)])[0], 1)
        self.cfg.write_text(json.dumps(self.CONFIG))
        self.assertEqual(run(configure_apps.main, ["--config", str(self.cfg), "--out", str(DASH / "out" / "b")])[0], 1)

    def test_the_example_config_is_accepted(self):
        code, out = run(configure_apps.main, ["--config", str(REPO / "config" / "config.example.json"),
                                              "--out", str(self.out), "--dry-run"])
        self.assertEqual(code, 0, out)
        self.assertIn("FieldApp (FLD-n): database collection fld", out)


if __name__ == "__main__":
    unittest.main()
