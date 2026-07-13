"""KN-2·KN-3·KN-4 — references/wiki/query_helper.py contract tests."""
import os
import subprocess
import sys
import unittest

HELPER_DIR = os.path.join(os.path.dirname(__file__), "..", "references", "wiki")
sys.path.insert(0, HELPER_DIR)

import query_helper as qh  # noqa: E402


class TestTokenize(unittest.TestCase):
    def test_latin_words_lowercased(self):
        toks = qh.tokenize("Caption Style 12pt")
        self.assertTrue({"caption", "style", "12pt"} <= toks)

    def test_cjk_one_and_two_grams(self):
        toks = qh.tokenize("디펜스 자료")
        # 1-grams
        self.assertTrue({"디", "펜", "스", "자", "료"} <= toks)
        # 2-grams (어절 내부만 — 공백을 건너는 bigram 없음)
        self.assertTrue({"디펜", "펜스", "자료"} <= toks)
        self.assertNotIn("스자", toks)

    def test_mixed_scripts(self):
        toks = qh.tokenize("IEEE 논문 rule")
        self.assertTrue({"ieee", "rule", "논", "문", "논문"} <= toks)

    def test_empty_and_none(self):
        self.assertEqual(qh.tokenize(""), set())
        self.assertEqual(qh.tokenize(None), set())


class TestMatch(unittest.TestCase):
    def _store(self, tmp):
        os.makedirs(tmp, exist_ok=True)
        with open(os.path.join(tmp, "defense-defect-patterns.md"), "w", encoding="utf-8") as f:
            f.write("# defense deck defect patterns\n디펜스 발표의 캡션 결함 반복\n")
        with open(os.path.join(tmp, "lab-style-spec.md"), "w", encoding="utf-8") as f:
            f.write("# lab style spec\ncaption 12pt black\n")
        with open(os.path.join(tmp, "not-markdown.txt"), "w", encoding="utf-8") as f:
            f.write("디펜스\n")  # .md 아님 — 매칭 대상 제외

    def test_ranks_by_overlap(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._store(tmp)
            hits = qh.match(tmp, "디펜스 캡션 결함")
            self.assertEqual(hits[0][0], "defense-defect-patterns.md")
            names = [n for n, _ in hits]
            self.assertNotIn("not-markdown.txt", names)

    def test_missing_dir_returns_empty(self):
        self.assertEqual(qh.match("/nonexistent/dir/for/omd-test", "질의"), [])

    def test_cli_match_smoke(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._store(tmp)
            out = subprocess.run(
                [sys.executable, os.path.join(HELPER_DIR, "query_helper.py"),
                 "match", tmp, "디펜스 캡션"],
                capture_output=True, text=True)
            self.assertEqual(out.returncode, 0)
            self.assertIn("defense-defect-patterns.md", out.stdout)


class TestSafeWikiPath(unittest.TestCase):
    def test_accepts_normal(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p = qh.safe_wiki_path(tmp, "convention", "lab-style-spec.md")
            self.assertTrue(p.endswith(os.path.join("convention", "lab-style-spec.md")))

    def test_rejects_traversal_shapes(self):
        for cat, name in [("convention", "../escape.md"),
                          ("convention", "a/b.md"),
                          ("convention", "a\\b.md"),
                          ("..", "x.md"),
                          ("convention", ".hidden.md"),
                          ("", "x.md")]:
            with self.assertRaises(ValueError, msg=f"{cat!r}/{name!r}"):
                qh.safe_wiki_path("/tmp/omd-wiki-root", cat, name)


class TestTitleToSlug(unittest.TestCase):
    def test_english_keywords(self):
        self.assertEqual(qh.title_to_slug("Defense deck defect patterns"),
                         "defense-deck-defect-patterns.md")

    def test_mixed_keeps_ascii_only(self):
        self.assertEqual(qh.title_to_slug("IEEE 캡션 rule"), "ieee-rule.md")

    def test_pure_korean_falls_back_to_hash(self):
        a = qh.title_to_slug("디펜스 자료 결함")
        b = qh.title_to_slug("디펜스 자료 결함")
        self.assertEqual(a, b)  # 결정론
        self.assertRegex(a, r"^note-[0-9a-f]{8}\.md$")

    def test_cli_slug(self):
        out = subprocess.run(
            [sys.executable, os.path.join(HELPER_DIR, "query_helper.py"),
             "slug", "Defense deck defect patterns"],
            capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "defense-deck-defect-patterns.md")


if __name__ == "__main__":
    unittest.main()
