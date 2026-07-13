"""Dogfooding guard (R2 acceptance, spec §5): omd's own README/CHANGELOG conform to the
repo-docs card's mechanical gate — the stdlib-checkable items run forever as pytest;
the borrowed-engine item (markdownlint) runs at dogfooding/release time via npx with
its log captured (AC-1b), degrading per D3 when unavailable."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
SEMVER_REGION = CHANGELOG.split("## Historical")[0]  # plan 결정 5: legacy 꼬리 구간 면제


def _readme_h2s():
    return [m.group(1).strip() for m in re.finditer(r"^## (.+)$", README, re.MULTILINE)]


def test_readme_required_sections_in_preset_order():
    """gate ①: library 프리셋 필수 섹션 존재 + 순서 (Install → Usage → … → License 마지막)."""
    heads = _readme_h2s()
    for required in ("Install", "Usage", "License"):
        assert any(required in h for h in heads), f"README: required section {required!r} missing"
    idx = {name: next(i for i, h in enumerate(heads) if name in h)
           for name in ("Install", "Usage", "License")}
    assert idx["Install"] < idx["Usage"] < idx["License"]
    assert "License" in heads[-1], "License must be the last section"


def test_readme_short_description_and_toc_rule():
    """gate ①: 제목 직후 짧은 설명(≤120자 한 줄) + 100줄 이상이면 ToC 필수."""
    lines = README.splitlines()
    assert lines[0].startswith("# "), "title must open the file"
    desc = next(l for l in lines[1:] if l.strip())
    assert len(desc) <= 120, f"short description is {len(desc)} chars (> 120, standard-readme)"
    if len(lines) >= 100:
        assert any("Table of Contents" in h or "목차" in h for h in _readme_h2s()), \
            "README ≥100 lines requires a ToC (standard-readme)"


def test_readme_no_placeholder_tokens():
    """gate ⑦ (PL-3): prompt 토큰 잔존 = FAIL. 링크 브래킷은 대상 아님(카드 Hard traps)."""
    assert not re.search(r"TODO|TBD|CHANGEME|lorem ipsum|your-\w+-here|\[Insert ", README)


def test_readme_code_fences_have_language_tags():
    """gate ④: 여는 펜스 전부 언어 태그."""
    fences = re.findall(r"^```(\S*)\s*$", README, re.MULTILINE)
    openers = fences[0::2]
    assert all(openers), f"un-tagged code fence(s): {fences}"


def test_readme_internal_links_resolve():
    """gate ②: 상대경로 내부 링크 실존 (외부 링크는 기본 게이트 제외 — spec §7 ③)."""
    for target in re.findall(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)", README):
        assert (ROOT / target.split("#")[0]).exists(), f"dangling internal link: {target}"


def test_changelog_unreleased_first_and_semver_descending():
    """gate ⑤: [Unreleased] 최상단 + semver 섹션 ISO 날짜 + 역순."""
    assert CHANGELOG.find("## [Unreleased]") < CHANGELOG.find("## [0.")
    entries = re.findall(r"^## \[(\d+)\.(\d+)\.(\d+)\] - \d{4}-\d{2}-\d{2}$",
                         SEMVER_REGION, re.MULTILINE)
    assert entries, "no dated semver sections found"
    versions = [tuple(map(int, e)) for e in entries]
    assert versions == sorted(versions, reverse=True), f"not descending: {versions}"


def test_changelog_semver_region_uses_keepachangelog_types_only():
    """gate ⑤: semver 구간의 ### 그룹은 6종만 (Historical 꼬리는 면제 — plan 결정 5)."""
    allowed = {"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"}
    types = set(re.findall(r"^### (\w+)$", SEMVER_REGION, re.MULTILINE))
    assert types <= allowed, f"non-keepachangelog types in semver region: {types - allowed}"


def test_changelog_historical_tail_preserved():
    """plan 결정 5: pre-semver 이력은 Historical 섹션에 verbatim 보존 (삭제 금지)."""
    assert "## Historical" in CHANGELOG
    assert "commit-SHA" in CHANGELOG  # 구 정책 언급 보존
