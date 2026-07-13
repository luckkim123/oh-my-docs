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


# ── R2: 장르 카드 계약 (repo-docs) ────────────────────────────────────
# 장르 카드의 엔진은 선택적 빌린 린터 체인(D3 degrade 보유)이라 GENERATION_CARDS의
# "핀 없으면 실패" 계약에 불편입(plan 결정 4) — 초기 UNVERIFIED 출발, dogfooding이
# 실측 가능한 엔진에 스탬프. 대신 필수 3섹션 + gate 완결성을 계약으로 고정.
GENRE_CARDS = ["repo-docs.md", "site.md"]


def test_genre_cards_carry_required_sections():
    for name in GENRE_CARDS:
        text = (FORMATS_DIR / name).read_text(encoding="utf-8")
        assert re.search(r"^## Engine\b", text, re.MULTILINE), f"{name}: '## Engine' missing"
        assert "## Hard traps" in text, f"{name}: 'Hard traps' missing"
        assert "## Version-snapshot policy" in text, f"{name}: snapshot policy missing"


def test_repo_docs_gate_is_deterministic_and_complete():
    text = (FORMATS_DIR / "repo-docs.md").read_text(encoding="utf-8")
    for token in (
        "## Verify gate",
        "placeholder",                        # PL-3 gate ⑦
        "ISO 8601",                           # gate ⑤
        "markdownlint",                       # gate ③
        "UNVERIFIED (engine unavailable)",    # D3 degrade
        "verify-runs/",                       # AC-1b
        "manifest",                           # D4/LC-2
        "McNutt",                             # ladder 1차 출처 (CHI 검증 반영)
        "License_Note",
    ):
        assert token in text, f"repo-docs.md: {token!r} missing"


def test_repo_docs_external_links_not_in_default_gate():
    # spec §7 ③: 외부 링크는 네트워크 의존 — 기본 게이트 제외, lychee 설치 시 선택
    text = (FORMATS_DIR / "repo-docs.md").read_text(encoding="utf-8")
    assert "lychee" in text and "optional" in text


# ── R3: site 장르 카드 계약 ──────────────────────────────────────────
def test_site_gate_is_deterministic_and_complete():
    text = (FORMATS_DIR / "site.md").read_text(encoding="utf-8")
    for token in (
        "## Verify gate",
        "mkdocs build --strict",              # gate ① — 1차 기계 게이트
        "Diátaxis",                           # 구조 프레임 (doc-planner 소비)
        "validation",                         # 표준 mkdocs.yml validation 블록
        "omitted_files",                      # gate ⑤ nav 완결성의 1차 커버
        "palette",                            # no-reference 폴백 (F8)
        "site-build",                         # built HTML 은 current/ 밖 (결정 4)
        "UNVERIFIED (engine unavailable)",    # D3 degrade
        "verify-runs/",                       # AC-1b
        "manifest",                           # D4 artifact-set
        "uvx",                                # 검증된 러너 형태 (결정 1)
    ):
        assert token in text, f"site.md: {token!r} missing"


def test_site_external_links_not_in_default_gate():
    # spec §7 ③ 동형: 외부 링크는 네트워크 의존 — 기본 게이트 제외, lychee 설치 시 선택
    text = (FORMATS_DIR / "site.md").read_text(encoding="utf-8")
    assert "lychee" in text and "optional" in text


def test_site_card_mkdocs_engine_stamped():
    """R3 실측 태스크의 완료 정의 — MkDocs 행이 이 머신에서 VERIFIED + 버전 핀."""
    text = (FORMATS_DIR / "site.md").read_text(encoding="utf-8")
    engine = _engine_section(text)
    mkdocs_rows = [l for l in engine.splitlines() if l.startswith("| MkDocs")]
    assert mkdocs_rows, "site.md: MkDocs engine row missing"
    assert "VERIFIED ✓" in mkdocs_rows[0], "MkDocs row not yet stamped"
    assert VERSION_RE.search(mkdocs_rows[0]), "MkDocs row pins no version"
