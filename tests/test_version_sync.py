"""Version SSOT — plugin.json's version field is the single source of truth (R1/H3).

omx precedent (test_version_sync.py), reduced per spec DT-1/DT-2: omd is a pure
plugin (no pyproject.toml) and README carries no version marker, so the only
mechanical check is "the SSOT field exists and is valid semver". Fan-out targets
are added here the day they exist — never injected preemptively (omx policy).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def test_version_field_exists():
    plugin = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    assert "version" in plugin, "plugin.json must carry the version SSOT field (H3)"


def test_version_is_valid_semver():
    plugin = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    assert SEMVER_RE.match(plugin.get("version", "")), (
        f"version must be MAJOR.MINOR.PATCH semver, got: {plugin.get('version')!r}"
    )
