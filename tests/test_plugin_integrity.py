"""Tests for plugin.json integrity — the skills field must be 1:1 with skills/.

Discovered while shipping the two-level wiki backport (2026-05-31): plugin.json's
skills list is explicit, so a skill directory that exists on disk but is not
registered here is **not loaded when the plugin is distributed** (`docs-learn` was
in skills/ but missing from plugin.json — its §4b local→global promotion path would
have shipped dead). This test blocks that drift. (Mirrors oms's test_plugin_integrity.)
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
SKILLS_DIR = ROOT / "skills"


def load_plugin() -> dict:
    return json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))


def registered_skills() -> set:
    """Directory-name set of plugin.json's skills field.

    Use Path(s).name (not str.strip) — strip() is a *character-set* strip and would
    mis-trim a name ending in a './' character (false no-drift). Path.name always
    yields just the last segment regardless of trailing slash / relative prefix."""
    return {Path(s).name for s in load_plugin()["skills"]}


def actual_skill_dirs() -> set:
    """skills/ subdirectories that actually carry a SKILL.md."""
    return {d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").exists()}


def test_every_skill_dir_is_registered():
    """A skill on disk but absent from plugin.json ships dead — forbid that drift."""
    missing = actual_skill_dirs() - registered_skills()
    assert not missing, f"skills present on disk but unregistered in plugin.json: {sorted(missing)}"


def test_every_registered_skill_exists():
    """A registered skill with no directory is a dangling reference — forbid it."""
    dangling = registered_skills() - actual_skill_dirs()
    assert not dangling, f"plugin.json registers skills with no directory: {sorted(dangling)}"


def test_docs_learn_is_registered():
    """Regression anchor: docs-learn (the two-level wiki promotion owner) must ship."""
    assert "docs-learn" in registered_skills()
