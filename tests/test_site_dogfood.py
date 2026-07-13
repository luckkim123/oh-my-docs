"""Site genre permanent guard — the committed pilot fixture (tests/fixtures/omd-site/)
must keep conforming to the site card's stdlib-checkable gate items forever.
Borrowed-engine items (mkdocs build --strict, markdownlint-cli2) run at dogfood/release
time via uvx/npx, NOT in the always-on suite (same rule as test_repo_docs_dogfood)."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
FIX = ROOT / "tests" / "fixtures" / "omd-site" / "current"
DOCS = FIX / "docs"
# PL-3 prompt tokens — same list as the repo-docs gate ⑦ (bare link brackets are legit)
PLACEHOLDER_RE = re.compile(r"\[Insert |TODO|TBD|CHANGEME|your-\w+-here|lorem ipsum", re.IGNORECASE)
# ponytail: naive line parse — the fixture nav must stay in the simple "- Title: path.md"
# form; upgrade to a yaml parser only if the fixture ever needs anchors/aliases.
NAV_MD_RE = re.compile(r"^\s*-\s+[^:]+:\s+(\S+\.md)\s*$", re.MULTILINE)


def _yml() -> str:
    return (FIX / "mkdocs.yml").read_text(encoding="utf-8")


def test_fixture_exists_with_config_and_docs():
    assert (FIX / "mkdocs.yml").is_file()
    assert (DOCS / "index.md").is_file()


def test_mkdocs_yml_pins_strict_validation_block():
    """카드 규칙: validation 블록 없는 --strict 는 nav 누락을 조용히 통과시킨다."""
    yml = _yml()
    assert "validation:" in yml
    assert "omitted_files: warn" in yml
    assert "anchors: warn" in yml


def test_nav_lists_every_docs_page():
    """gate ⑤ 의 stdlib 이중 체크 — 엔진 없이도 fixture 회귀를 잡는다."""
    nav_pages = set(NAV_MD_RE.findall(_yml()))
    disk_pages = {str(p.relative_to(DOCS)) for p in DOCS.rglob("*.md")}
    assert nav_pages == disk_pages, f"nav vs docs/ drift: {nav_pages ^ disk_pages}"


def test_diataxis_quadrants_present():
    for quadrant in ("tutorials", "how-to", "reference", "explanation"):
        assert (DOCS / quadrant).is_dir(), f"quadrant {quadrant!r} missing"


def test_no_placeholder_tokens():
    for page in DOCS.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        assert not PLACEHOLDER_RE.search(text), f"{page.name}: placeholder token (PL-3)"


def test_internal_md_links_resolve():
    for page in DOCS.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)", text):
            if target.startswith(("http://", "https://")):
                continue
            assert (page.parent / target).resolve().is_file(), f"{page.name} → {target} broken"


def test_code_fences_carry_language_tags():
    for page in DOCS.rglob("*.md"):
        lines = page.read_text(encoding="utf-8").splitlines()
        opener = True
        for ln in lines:
            if ln.strip().startswith("```"):
                if opener:
                    assert ln.strip() != "```", f"{page.name}: untagged code fence"
                opener = not opener
