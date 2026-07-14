"""G3 — references/wiki/lint_wiki.py: report-only auditor for .omd/wiki stores."""
import os
import subprocess
import sys
import tempfile
import time
import unittest

HELPER_DIR = os.path.join(os.path.dirname(__file__), "..", "references", "wiki")
sys.path.insert(0, HELPER_DIR)

import lint_wiki  # noqa: E402

NOW = "2026-07-14T00:00:00"


def build_store(root):
    """Fixture: one healthy note, one stale schema-less note, one oversized,
    one broken-ref, one near-dup pair, one misplaced file, one unknown dir."""
    conv = os.path.join(root, "convention")
    dec = os.path.join(root, "decision")
    os.makedirs(conv); os.makedirs(dec)
    os.makedirs(os.path.join(root, "scratch"))          # unknown-category
    w = lambda p, s: open(p, "w", encoding="utf-8").write(s)
    w(os.path.join(root, "loose.md"), "misplaced\n")     # misplaced
    w(os.path.join(conv, "lab-style-spec.md"),
      "---\nconfidence: high\n---\n# lab style\ncaption 12pt, see [[defense-defect-patterns]]\n")
    w(os.path.join(conv, "defense-defect-patterns.md"),
      "# defense defects\nno confidence marker here\n")  # missing-confidence
    w(os.path.join(conv, "defense-defect-patterns-two.md"),
      "# near dup of the above\n")                       # near-duplicate + missing-confidence
    w(os.path.join(dec, "big-note.md"), "x" * 11000)     # oversized
    w(os.path.join(dec, "arc-choice.md"), "see [[no-such-page]]\n")  # broken-ref
    old = time.mktime(time.strptime("2026-01-01", "%Y-%m-%d"))
    os.utime(os.path.join(conv, "defense-defect-patterns.md"), (old, old))  # stale


class TestScan(unittest.TestCase):
    def types(self, issues):
        return {t for _, t, _, _ in issues}

    def test_detects_expected_issue_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_store(tmp)
            issues = lint_wiki.scan(tmp, now=NOW)
            self.assertTrue({"misplaced", "unknown-category", "stale", "oversized",
                             "broken-ref", "near-duplicate", "missing-confidence"}
                            <= self.types(issues))

    def test_orphan_only_with_link_culture(self):
        with tempfile.TemporaryDirectory() as tmp:
            conv = os.path.join(tmp, "convention"); os.makedirs(conv)
            open(os.path.join(conv, "solo-note.md"), "w").write("no links anywhere\n")
            old = time.mktime(time.strptime("2026-01-01", "%Y-%m-%d"))
            os.utime(os.path.join(conv, "solo-note.md"), (old, old))
            # 링크 문화 없음 → orphan 미발화
            self.assertNotIn("orphan", self.types(lint_wiki.scan(tmp, now=NOW)))

    def test_missing_root_is_single_info(self):
        issues = lint_wiki.scan("/nonexistent/omd-wiki", now=NOW)
        self.assertEqual([i[1] for i in issues], ["empty"])
        self.assertEqual(issues[0][0], "info")

    def test_cli_reports_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_store(tmp)
            out = subprocess.run(
                [sys.executable, os.path.join(HELPER_DIR, "lint_wiki.py"),
                 "--root", tmp, "--now", NOW],
                capture_output=True, text=True)
            self.assertEqual(out.returncode, 0)   # report-only: 이슈가 있어도 0
            self.assertIn("near-duplicate", out.stdout)
            self.assertIn("total", out.stdout)    # 요약 줄


if __name__ == "__main__":
    unittest.main()
