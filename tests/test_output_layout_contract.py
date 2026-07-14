"""Output-layout contract (R2 D4): the layout card defines the artifact-set
generalization — multi-file genres get a `current/` directory entry point, a
manifest with per-file hashes and roles, directory-wise version snapshots (LC-1),
and a verify-runs/ log area (AC-1b). Content assertions in the same style as
test_format_cards.py — the card is a data file, its strings ARE the contract."""
from pathlib import Path

CARD = (Path(__file__).parent.parent / "references" / "output-layout.md").read_text(encoding="utf-8")


def test_invariant_redefined_as_one_current_entry():
    # D4: "사용자가 보는 진입점은 정확히 하나의 current 엔트리" — 단일 파일이든 디렉토리든
    assert "current entry" in CARD
    assert "current/" in CARD


def test_manifest_schema_fields_locked():
    for token in ('"slug"', '"format"', '"paths"', '"path"', '"sha256"', '"role"'):
        assert token in CARD, f"manifest schema field {token} missing"
    assert "manifest.json" in CARD


def test_manifest_written_atomically():
    # ST-1: half-written manifest = G6 ownership guard silently disabled
    assert "os.replace" in CARD


def test_artifact_set_snapshot_is_directory_copy():
    # LC-1: 다중 파일 스냅샷은 versions/ 디렉토리 통째 복사
    assert "v{NN}_{YYYY-MM-DD}_{summary}/" in CARD


def test_verify_runs_log_area_defined():
    # AC-1b: 빌린 엔진 stdout/stderr 캡처 위치
    assert "verify-runs/" in CARD


def test_role_field_carries_placement():
    # LC-2: 배치(저장소 상대경로)는 role이 담고, 복사는 사용자 책임
    assert "role" in CARD and "cp -r" in CARD


def test_single_file_formats_unchanged():
    # 하위 호환: 오피스 단일 파일 경로 보존
    assert "current.<ext>" in CARD


def test_ownership_guard_section_present():
    """G6: overwrite/delete under an artifact-set current/ must consult the manifest."""
    assert "### 3.4 Ownership guard (G6)" in CARD
    assert "AskUserQuestion" in CARD.split("### 3.4")[1].split("## 4.")[0]


def test_ownership_guard_consumers_wired():
    root = Path(__file__).parent.parent
    for rel in ("skills/docs-build/SKILL.md", "skills/docs-revise/SKILL.md",
                "agents/doc-builder.md"):
        body = (root / rel).read_text(encoding="utf-8")
        assert "3.4" in body and "manifest" in body.lower(), rel
