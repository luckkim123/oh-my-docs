"""Genre generalization guards (R2 §4.4) — skill bodies delegate format specifics
to the card instead of hardcoding office assumptions (D1: no per-format if/else).
Each backport task appends its section; content assertions in the same style as
test_agent_contract.py. Office contracts stay present (backward compat)."""
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def _ref(rel: str) -> str:
    return (ROOT / "references" / rel).read_text(encoding="utf-8")


# ── T4: docs-verify / docs-inspect (§4.4-5, PS-1·PS-3) ────────────────

def test_verify_skill_gate_is_card_defined():
    body = _skill("docs-verify")
    assert "card-defined verify gate" in body
    assert "repo-docs-rubric" in body or "repo-docs" in body
    assert "zip CRC" in body  # 오피스 계약은 예시로 보존


def test_inspect_skill_lens_composition_is_dynamic():
    body = _skill("docs-inspect")
    assert "rubric card" in body
    assert "PS-3" in body
    assert "PPTEval" in body  # 오피스 3축은 그 카드의 사례로 보존
