"""references/snippets/engine_check.py — the G7 engine-version-drift check.
Fully pure-logic (regex parsing + dict diff, no external engine invoked) — no skip needed,
runs unconditionally on clean CI.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "references" / "snippets"))
sys.path.insert(0, str(ROOT / "tests"))
import engine_check  # noqa: E402
from test_format_cards import FORMATS_DIR, GENERATION_CARDS  # noqa: E402

FIXTURE_CARD = """\
## Engine

| Tool | Role | Verified on this machine (2026-05-28) |
|:---|:---|:---|
| `python-pptx` 1.0.2 | create / edit shapes | ✓ installed |
| `matplotlib` 3.9.4 + `Pillow` 11.3 | LaTeX math → PNG | ✓ installed |
| `soffice` (LibreOffice) | .pptx → .pdf for rendering | resolve on PATH |
| `pdftoppm` | .pdf → .png | resolve on PATH |

## Hard traps
Nothing relevant here.
"""


def test_parse_engine_pins_hand_built_fixture():
    pins = engine_check.parse_engine_pins(FIXTURE_CARD)
    assert pins["python-pptx"] == "1.0.2"
    assert pins["matplotlib"] == "3.9.4"
    assert pins["Pillow"] == "11.3"
    # presence-only rows have nothing to diff against — skipped, not a bogus pin
    assert "soffice" not in pins
    assert "pdftoppm" not in pins


def test_parse_engine_pins_against_real_cards():
    # Proves it works on the live cards, not just a hand-built fixture string. hwpx.md's
    # own Engine row wraps its version in prose ("PyPI 2.9.1 published"), not the
    # backtick-adjacent `` `tool` X.Y.Z `` shape the other 3 cards use — so it legitimately
    # yields no pins here (a dict, not a crash); only pptx/docx/xlsx are asserted non-empty.
    for name in GENERATION_CARDS:
        text = (FORMATS_DIR / name).read_text(encoding="utf-8")
        pins = engine_check.parse_engine_pins(text)
        assert isinstance(pins, dict)
    for name in ("pptx.md", "docx.md", "xlsx.md"):
        text = (FORMATS_DIR / name).read_text(encoding="utf-8")
        pins = engine_check.parse_engine_pins(text)
        assert pins, f"{name}: parse_engine_pins found no pins"


def test_live_version_cmd_dispatch_absent_binary_returns_none():
    assert engine_check.live_version("cmd:definitely-not-a-real-binary-xyz") is None


def test_live_version_import_dispatch_absent_module_returns_none():
    assert engine_check.live_version("definitely-not-a-real-module-xyz") is None


def test_check_engine_drift_detects_mismatch():
    pinned = {"python-pptx": "1.0.2", "matplotlib": "3.9.4"}
    live = {"python-pptx": "1.1.0", "matplotlib": "3.9.4"}
    mismatches = engine_check.check_engine_drift(FIXTURE_CARD, live)
    assert any("python-pptx" in m for m in mismatches)
    assert not any("matplotlib" in m for m in mismatches)
    _ = pinned  # documents intent; check_engine_drift re-parses pins from card_text itself


def test_check_engine_drift_empty_when_versions_agree():
    live = {"python-pptx": "1.0.2", "matplotlib": "3.9.4", "Pillow": "11.3"}
    assert engine_check.check_engine_drift(FIXTURE_CARD, live) == []
