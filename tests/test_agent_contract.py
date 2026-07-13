"""Agent contract guards (R1): frontmatter model policy (G4 precondition) and, from
Task 11, the Final_Response_Contract markers (AC-1a). stdlib frontmatter parse only.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
AGENTS_DIR = ROOT / "agents"

# Deliberate judgment lanes (inspector/verifier) run opus; production lanes run sonnet.
# doc-planner is sonnet by default — Deliberate consensus escalates at Task-call time
# (skills/docs-plan SKILL.md --consensus path), never via frontmatter.
EXPECTED_MODELS = {
    "doc-analyzer": "sonnet",
    "doc-builder": "sonnet",
    "doc-planner": "sonnet",
    "doc-inspector": "opus",
    "doc-verifier": "opus",
}


def _frontmatter(name: str) -> dict:
    lines = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", f"{name}: frontmatter must open the file"
    fm = {}
    for line in lines[1:]:
        if line == "---":
            return fm
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    raise AssertionError(f"{name}: unterminated frontmatter")


def test_agent_model_policy():
    for name, model in EXPECTED_MODELS.items():
        assert _frontmatter(name).get("model") == model, (
            f"{name}: frontmatter model must be {model} (spec §3.1 G4 / critique #2)"
        )


# Final_Response_Contract (AC-1a): the markers each agent's Output_Format promises.
# These are the strings downstream consumers (skills, humans) grep for — losing one
# in a doc rewrite is a silent contract break (exactly how H2 happened).
REQUIRED_MARKERS = {
    "doc-verifier": ["### Verdict", "**Status**: PASS | FAIL"],
    "doc-inspector": ["## Formative Review"],
    "doc-planner": ["## Narrative Arc", "## Outline", "## Coverage Check"],
    "doc-analyzer": ["## Source Inventory", "## Reference Design System"],
    "doc-builder": ["## Artifact", "## Build Notes"],
}

# Self-approval ban is load-bearing prose for the two review lanes only (spec §3.4 AC-1a).
SELF_APPROVAL_BANS = {
    "doc-verifier": "never self-approve",
    "doc-inspector": "never approve work",
}


def _body(name: str) -> str:
    return (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def test_final_response_contract_markers():
    for name, markers in REQUIRED_MARKERS.items():
        body = _body(name)
        for marker in markers:
            assert marker in body, f"{name}: required output marker {marker!r} missing"


def test_self_approval_ban_present():
    for name, phrase in SELF_APPROVAL_BANS.items():
        assert phrase in _body(name), f"{name}: self-approval ban phrase {phrase!r} missing"


# ── R2 (§4.4-3·4): 뒷단 쌍의 카드 위임 일반화 계약 ─────────────────────
# doc-verifier.md:46이 self-gate(builder)/독립재검증(verifier)을 쌍으로 명시하므로
# 두 파일은 같은 커밋에서 함께 일반화된다(PS-5) — 이 마커들이 쌍의 존재 증거.
GENERALIZATION_MARKERS = {
    "doc-verifier": [
        "card-defined verify gate",          # F3: integrity를 카드 위임으로
        "manifest.json",                     # AC-5: artifact-set 스냅샷 식별자
        "verify-runs/",                      # AC-1b: 빌린 엔진 로그 캡처
        "UNVERIFIED (engine unavailable)",   # D3: 엔진 미설치 degrade verdict
    ],
    "doc-builder": [
        "artifact-set",                      # D4: 다중 파일 산출 계약
        "manifest.json",
        "os.replace",                        # ST-1: manifest atomic write
    ],
}


def test_backend_pair_generalized_to_card_delegation():
    for name, markers in GENERALIZATION_MARKERS.items():
        body = _body(name)
        for marker in markers:
            assert marker in body, f"{name}: R2 generalization marker {marker!r} missing"


def test_backend_pair_keeps_office_contract():
    # 하위 호환: 오피스 계열 계약(5-check·shape assertion)은 카드 위임 후에도 서술 보존
    assert "zip CRC" in _body("doc-verifier")
    assert "assert_shapes.py" in _body("doc-builder")
