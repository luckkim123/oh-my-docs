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


# ── T5: docs-standardize / docs-revise (§4.4-6·7, F6/PS-2·PS-4) ───────

def test_standardize_gate_branches_by_render_capability():
    body = _skill("docs-standardize")
    assert "convention checklist" in body   # 텍스트 장르 대체 게이트 (F6/PS-2)
    assert "85%" in body                    # 렌더 가능 포맷의 기존 게이트 보존
    assert "office" in body.lower()


def test_revise_pass_definition_tracks_verifier():
    body = _skill("docs-revise")
    assert "card-defined verify gate" in body
    assert "PS-4" in body
    # recur-방지(포맷 불가지론) 항목은 유지
    assert "does not recur" in body


# ── T7: repo-docs 루브릭 (PS-3 동적 렌즈) ─────────────────────────────

def test_repo_docs_rubric_exists_and_splits_axes():
    text = _ref("rubrics/repo-docs-rubric.md")
    assert "verify gate" in text          # 기계 축은 카드 게이트 소관 명시
    assert "Treude" in text               # 차원 프레임 원출처 (7축 아님 — CHI 검증 반영)
    assert "no self-approval" in text     # ppteval과 동일한 분리 규칙
    for lens in ("Welcoming", "Information scent", "Honesty"):
        assert lens in text, f"qualitative lens {lens!r} missing"
