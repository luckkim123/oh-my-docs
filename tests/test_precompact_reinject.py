"""G2 — hooks/precompact_reinject.py: notepad pruning + compaction-survival reinject."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(__file__), "..", "hooks", "precompact_reinject.py")
PLUGIN_JSON = os.path.join(os.path.dirname(__file__), "..", ".claude-plugin", "plugin.json")

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


class TestRegistration(unittest.TestCase):
    def test_plugin_json_registers_both_events(self):
        cfg = json.load(open(PLUGIN_JSON, encoding="utf-8"))
        hooks = cfg["hooks"]
        flat = json.dumps(hooks.get("PreCompact", [])) + json.dumps(hooks.get("SessionStart", []))
        self.assertEqual(flat.count("precompact_reinject.py"), 2)
        # SessionStart는 compact 매처만 — startup 마다 발화하지 않게
        self.assertEqual(hooks["SessionStart"][0]["matcher"], "compact")


if __name__ == "__main__":
    unittest.main()
