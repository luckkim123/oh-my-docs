"""G2 — hooks/docs_precompact_reinject.py: notepad pruning + compaction-survival reinject."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HOOK = os.path.join(os.path.dirname(__file__), "..", "hooks", "docs_precompact_reinject.py")
PLUGIN_JSON = os.path.join(os.path.dirname(__file__), "..", ".claude-plugin", "plugin.json")
HOOK_DIR = os.path.join(os.path.dirname(__file__), "..", "hooks")
sys.path.insert(0, HOOK_DIR)

import docs_precompact_reinject  # noqa: E402

NOTEPAD = """# omd notepad

## Priority Context
- no in-place modification of the original
- final is a single outputs/deck/current.pptx; gate 2 passed

## Working Notes
{working}

## Manual
- user's own line — never touched
"""


def run_hook(payload):
    return subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                          capture_output=True, text=True)


def write_notepad(cwd, working_lines):
    os.makedirs(os.path.join(cwd, ".omd"), exist_ok=True)
    body = NOTEPAD.format(working="\n".join(working_lines))
    with open(os.path.join(cwd, ".omd", "notepad.md"), "w", encoding="utf-8") as f:
        f.write(body)
    return os.path.join(cwd, ".omd", "notepad.md")


class TestReinject(unittest.TestCase):
    def test_session_start_compact_reinjects_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_notepad(tmp, ["- note"])
            out = run_hook({"hook_event_name": "SessionStart", "source": "compact",
                            "cwd": tmp})
            self.assertEqual(out.returncode, 0)
            payload = json.loads(out.stdout)
            ctx = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("no in-place modification", ctx)
            self.assertNotIn("user's own line", ctx)  # Priority만 재주입

    def test_no_notepad_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = run_hook({"hook_event_name": "SessionStart", "source": "compact",
                            "cwd": tmp})
            self.assertEqual(out.returncode, 0)
            self.assertEqual(out.stdout.strip(), "")

    def test_broken_payload_fails_open(self):
        out = subprocess.run([sys.executable, HOOK], input="not json{",
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)


class TestPrune(unittest.TestCase):
    def test_oversized_working_notes_trimmed_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            lines = [f"- working item {i} " + "x" * 300 for i in range(60)]  # ≈19KiB > 16KiB
            path = write_notepad(tmp, lines)
            out = run_hook({"hook_event_name": "PreCompact", "trigger": "auto",
                            "cwd": tmp})
            self.assertEqual(out.returncode, 0)
            body = open(path, encoding="utf-8").read()
            self.assertIn("no in-place modification", body)   # Priority 불변
            self.assertIn("user's own line", body)            # Manual 불변
            self.assertIn("working item 59", body)            # 최신 유지
            self.assertNotIn("working item 0", body)          # 오래된 것 절단
            self.assertLess(len(body.encode("utf-8")), 17000)

    def test_small_notepad_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_notepad(tmp, ["- one line"])
            before = open(path, encoding="utf-8").read()
            run_hook({"hook_event_name": "PreCompact", "trigger": "manual", "cwd": tmp})
            self.assertEqual(open(path, encoding="utf-8").read(), before)


class TestFailureModes(unittest.TestCase):
    def test_dir_shaped_notepad_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".omd", "notepad.md"))  # dir, not a file
            out1 = run_hook({"hook_event_name": "SessionStart", "source": "compact", "cwd": tmp})
            self.assertEqual(out1.returncode, 0)
            self.assertEqual(out1.stdout.strip(), "")
            out2 = run_hook({"hook_event_name": "PreCompact", "trigger": "auto", "cwd": tmp})
            self.assertEqual(out2.returncode, 0)
            self.assertEqual(out2.stdout.strip(), "")

    @unittest.skipUnless(not hasattr(os, "geteuid") or os.geteuid() != 0,
                          "chmod cannot block root")
    def test_prune_write_failure_leaves_original_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            lines = [f"- working item {i} " + "x" * 300 for i in range(60)]
            path = write_notepad(tmp, lines)
            before = open(path, encoding="utf-8").read()
            omd_dir = os.path.join(tmp, ".omd")
            os.chmod(omd_dir, 0o555)  # read+exec only — mkstemp() can't create a file here
            try:
                out = run_hook({"hook_event_name": "PreCompact", "trigger": "auto", "cwd": tmp})
                self.assertEqual(out.returncode, 0)
                self.assertEqual(open(path, encoding="utf-8").read(), before)
                self.assertEqual([f for f in os.listdir(omd_dir) if ".tmp" in f], [])
            finally:
                os.chmod(omd_dir, 0o755)

    def test_prune_replace_failure_rolls_back_and_reraises(self):
        """os.replace() failing mid-write (disk full, etc.) must clean up the
        temp file and re-raise — never leave a half-written notepad or a
        leaked *.tmp (lines 83-88's except/unlink/raise)."""
        with tempfile.TemporaryDirectory() as tmp:
            lines = [f"- working item {i} " + "x" * 300 for i in range(60)]
            path = write_notepad(tmp, lines)
            before = open(path, encoding="utf-8").read()
            with mock.patch("os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    docs_precompact_reinject.prune(path)
            self.assertEqual(open(path, encoding="utf-8").read(), before)
            omd_dir = os.path.dirname(path)
            self.assertEqual([f for f in os.listdir(omd_dir) if ".tmp" in f], [])

    def test_missing_working_notes_section_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".omd"), exist_ok=True)
            path = os.path.join(tmp, ".omd", "notepad.md")
            padding = "\n".join(f"- manual pad {i} " + "x" * 300 for i in range(60))
            body = (
                "# omd notepad\n\n"
                "## Priority Context\n"
                "- no in-place modification of the original\n\n"
                "## Manual\n"
                "- user's own line — never touched\n"
                f"{padding}\n"
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            self.assertGreater(os.path.getsize(path), 16 * 1024)  # oversized, no Working Notes
            before = open(path, encoding="utf-8").read()
            out = run_hook({"hook_event_name": "PreCompact", "trigger": "auto", "cwd": tmp})
            self.assertEqual(out.returncode, 0)
            after = open(path, encoding="utf-8").read()
            self.assertEqual(after, before)  # Priority/Manual intact — only Working Notes is prunable
            self.assertGreater(os.path.getsize(path), 16 * 1024)  # still over cap

    def test_second_prune_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            lines = [f"- working item {i} " + "x" * 300 for i in range(60)]
            path = write_notepad(tmp, lines)
            docs_precompact_reinject.prune(path)
            after_first = open(path, encoding="utf-8").read()
            docs_precompact_reinject.prune(path)
            after_second = open(path, encoding="utf-8").read()
            self.assertEqual(after_second, after_first)


class TestRegistration(unittest.TestCase):
    def test_plugin_json_registers_both_events(self):
        cfg = json.load(open(PLUGIN_JSON, encoding="utf-8"))
        hooks = cfg["hooks"]
        flat = json.dumps(hooks.get("PreCompact", [])) + json.dumps(hooks.get("SessionStart", []))
        self.assertEqual(flat.count("docs_precompact_reinject.py"), 2)
        # SessionStart는 compact 매처만 — startup 마다 발화하지 않게
        self.assertEqual(hooks["SessionStart"][0]["matcher"], "compact")


if __name__ == "__main__":
    unittest.main()
