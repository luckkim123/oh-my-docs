"""Skill-contract guard (R2 §3.2 + AC-4): every concrete references/ path a skill or
agent body names must exist on disk. H7 (themes unwired) and the omx "skills reference
nonexistent verbs" incident are the motivating drifts. Placeholder tokens
(<format>, {name}, *) are skipped — only concrete paths are checked. Scan covers
agents/*.md too (AC-4 — dead cross-references die the same way)."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCANNED = sorted((ROOT / "skills").glob("*/SKILL.md")) + sorted((ROOT / "agents").glob("*.md"))
REF_RE = re.compile(r"references/[A-Za-z0-9_\-./<>{}*]+")


def _concrete_refs(text):
    for m in REF_RE.finditer(text):
        path = m.group(0).rstrip(".,;:)")
        if any(ch in path for ch in "<>{}*"):
            continue
        yield path


def test_scan_targets_exist():
    assert SCANNED, "no skills/agents found — scan roots moved?"


def test_referenced_paths_exist():
    missing = []
    for f in SCANNED:
        for ref in _concrete_refs(f.read_text(encoding="utf-8")):
            if not (ROOT / ref).exists():
                missing.append(f"{f.relative_to(ROOT)} → {ref}")
    assert not missing, "dangling references:\n" + "\n".join(sorted(set(missing)))


def test_docs_learn_calls_wiki_lint():
    """G3: docs-learn's steps run the report-only linter before promotion review."""
    body = (ROOT / "skills" / "docs-learn" / "SKILL.md").read_text(encoding="utf-8")
    assert "lint_wiki.py" in body
    assert "report-only" in body
