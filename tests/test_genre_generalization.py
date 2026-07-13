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


def test_site_rubric_exists_and_splits_axes():
    text = _ref("rubrics/site-rubric.md")
    assert "verify gate" in text          # 기계 축(빌드/링크)은 카드 게이트 소관 명시
    assert "Diátaxis" in text             # 정보 구조 축의 프레임 원출처
    assert "no self-approval" in text     # ppteval·repo-docs 와 동일한 분리 규칙
    for lens in ("Information architecture", "Prose quality"):
        assert lens in text, f"qualitative lens {lens!r} missing"


# ── T8: 앞단 스킬 (§4.4-8/F7 — 발표 어휘 하드코딩 해소) ────────────────

def test_intake_genre_frames_from_card():
    body = _skill("docs-intake")
    assert "the card defines" in body        # F7: 카드가 장르별 intake 질문 정의
    assert "artifact-set scope" in body      # 세트 장르 스코프 게이트 (비평 #4)
    assert "weakest component" in body       # PL-1: 컴포넌트 최솟값 판정
    assert "PR-1" in body                    # 재수렴 신호
    assert "defense/conference/lecture" in body  # 오피스 사례 보존


def test_intake_names_site_frame():
    body = _skill("docs-intake")
    assert "Diátaxis" in body                # site 의 장르 프레임
    assert "repo-docs, site" in body         # 세트 스코프 게이트가 site 도 커버


def test_plan_structure_frame_from_card():
    body = _skill("docs-plan")
    assert "structure frame" in body
    assert "section preset" in body          # repo-docs 프레임
    assert "narrative arc" in body           # 오피스 프레임 보존


# ── T9: 앞단 에이전트 (§4.4-8/F7·AC-3) ────────────────────────────────

def _agent(name: str) -> str:
    return (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")


def test_planner_success_criteria_generalized():
    body = _agent("doc-planner")
    assert "structure frame" in body
    assert "section preset" in body
    assert "## Narrative Arc" in body        # AC-1a 헤딩 보존


def test_analyzer_has_input_boundary_and_genre_frame():
    body = _agent("doc-analyzer")
    assert "Input boundary" in body          # AC-3 화이트리스트
    assert "never read the whole codebase" in body
    assert "genre frame" in body


def test_analyzer_genre_frame_covers_site():
    body = _agent("doc-analyzer")
    assert "Diátaxis" in body
    assert "mkdocs.yml" in body              # site 입력 화이트리스트의 구체물


# ── T11: 소형 묶음 (§4.4-10~13) ───────────────────────────────────────

def test_build_knowledge_table_lists_repo_docs():
    body = _skill("docs-build")
    assert "repo-docs" in body and "references/formats/repo-docs.md" in body


def test_build_knowledge_table_lists_site():
    body = _skill("docs-build")
    assert "references/formats/site.md" in body
    assert "site-build" in body              # built HTML 은 current/ 밖 (결정 4)


def test_build_gate_generalized_beyond_png():
    body = _skill("docs-build")
    assert "fresh-read" in body              # 텍스트 장르 sanity 증거
    assert "PNG" in body                     # 오피스 증거는 보존


def test_learning_protocol_has_text_genre_boundary():
    text = _ref("learning-protocol.md")
    assert "badge style" in text            # 학습 가능 FORM 예시
    assert "link targets" in text           # 금지 CONTENT 예시


def test_convert_translate_reject_artifact_sets():
    for name in ("docs-convert", "docs-translate"):
        body = _skill(name)
        assert "artifact-set" in body and "unsupported" in body, f"{name}: LC-3 guard missing"


def test_themes_declared_office_only():
    text = _ref("themes/README.md")
    assert "Office formats only" in text
    assert "repo-docs" in text              # 텍스트 장르 폴백의 소재지 명시 (F8)
