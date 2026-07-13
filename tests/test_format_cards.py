"""Format card contract (G7) — every generation card pins its engine versions, and
the card-authoring contract (references/formats/README.md) defines the engine-drift
demotion rule. Locked BEFORE R2/R3 double the card count (retrofit is expensive).
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
FORMATS_DIR = ROOT / "references" / "formats"
GENERATION_CARDS = ["pptx.md", "docx.md", "xlsx.md", "hwpx.md"]  # pdf.md is input-side (H5)
VERSION_RE = re.compile(r"\d+\.\d+")


def _engine_section(text: str) -> str:
    m = re.search(r"^## Engine\b(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert m, "card must carry an '## Engine' section"
    return m.group(1)


def test_generation_cards_pin_engine_versions():
    for name in GENERATION_CARDS:
        text = (FORMATS_DIR / name).read_text(encoding="utf-8")
        engine = _engine_section(text)
        assert VERSION_RE.search(engine), f"{name}: Engine section pins no version number"


def test_card_contract_defines_engine_drift_rule():
    contract = (FORMATS_DIR / "README.md").read_text(encoding="utf-8")
    assert "UNVERIFIED (engine drift)" in contract
    assert "## Engine" in contract  # 필수 섹션 계약 명시
