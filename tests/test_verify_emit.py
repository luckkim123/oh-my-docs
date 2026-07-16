"""Tests for the document-integrity PostToolUse hook (docs_verify_emit.py).

핵심 계약: 문서 산출/변환 Bash 명령일 때만 무결성 리마인더를 주입하고, 그 외엔
침묵한다(노이즈 제어). 2026-06-16 검수에서 드러난 두 결함을 회귀 고정한다:
  (1) 빌더 권장 경로 `python3 build.py` 는 명령에 엔진 문자열도 .pptx 도 안 나타나
      옛 "신호 AND 확장자" 조건에 안 잡혔다 — 하네스가 시키는 바로 그 경로가
      탐지 사각이었다. 이제 doc-네임 스크립트 실행도 잡는다.
  (2) 단, 무관한 `python3 analyze_runs.py` 는 여전히 침묵해야 한다(과발동 금지).
또한 리마인더가 shape 어서션(font.size·width>0·폰트 일치)을 안내해야 한다 —
PNG 육안으로 안 잡히는 v4/v5 회귀를 막는 게이트.
stdlib only, fail-open.

isomorphic 출처: tests/test_route_emit.py (같은 subprocess 패턴).
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from hooks.docs_verify_emit import is_doc_build
import hooks.docs_verify_emit as mod

HOOK = Path(__file__).parent.parent / "hooks" / "docs_verify_emit.py"


def run_hook(command: str, tool_name: str = "Bash", cwd: Optional[str] = None, env: Optional[dict] = None) -> str:
    """훅을 서브프로세스로 실행하고 stdout 반환 (fail-open: rc는 항상 0)."""
    payload = {"tool_name": tool_name, "tool_input": {"command": command}}
    if cwd is not None:
        payload["cwd"] = cwd
    run_env = None
    if env is not None:
        run_env = {**os.environ, **env}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True,
        env=run_env,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return proc.stdout


def fires(command: str, tool_name: str = "Bash", cwd: Optional[str] = None) -> bool:
    """리마인더가 주입됐는지 (stdout 비어있으면 침묵)."""
    return run_hook(command, tool_name=tool_name, cwd=cwd).strip() != ""


# ── 발동해야 하는 명령들 ──────────────────────────────────────────────
# cwd=tmp_path로 각 테스트를 격리: HG-3 쿨다운은 리마인더 문구(모든 build 명령이
# 동일 문구)를 content-hash로 묶으므로, 격리 없이 같은 프로세스에서 반복 호출하면
# 서로를 침묵시킨다 — 실제 프로덕션 의미론(중복 억제)이 테스트 간 누설되지 않게 함.

def test_fires_on_builder_recipe_script(tmp_path):
    """① 빌더 권장 경로 `python3 build.py` 발동 (옛 탐지 사각 — 2026-06-16 D6①)."""
    assert fires("python3 build.py", cwd=str(tmp_path / "a"))
    assert fires("python3 .omd/deck/build_deck.py", cwd=str(tmp_path / "b"))
    assert fires("python build_slides.py", cwd=str(tmp_path / "c"))
    assert fires("python3 make_presentation.py", cwd=str(tmp_path / "d"))


def test_fires_on_inline_engine_signal(tmp_path):
    """② 인라인 엔진 신호 발동 (-c 'from pptx ...' 회귀 방지)."""
    assert fires("python3 -c 'from pptx import Presentation'", cwd=str(tmp_path))


def test_fires_on_convert(tmp_path):
    """③ soffice 변환 발동."""
    assert fires("soffice --headless --convert-to pdf deck.pptx", cwd=str(tmp_path))


# ── 침묵해야 하는 명령들 (노이즈 제어) ────────────────────────────────

def test_silent_on_readonly_render(tmp_path):
    """④ read-only 렌더/무결성 검사는 침묵."""
    assert not fires("pdftoppm -png -r 150 deck.pdf slide", cwd=str(tmp_path))
    assert not fires("unzip -t deck.pptx", cwd=str(tmp_path))


def test_silent_on_unrelated_script(tmp_path):
    """⑤ 문서와 무관한 스크립트 실행은 침묵 (과발동 금지)."""
    assert not fires("python3 analyze_runs.py", cwd=str(tmp_path))
    assert not fires("python3 train.py", cwd=str(tmp_path))


def test_silent_on_non_exec(tmp_path):
    """⑥ 실행이 아닌 명령은 침묵."""
    assert not fires("ls *.py", cwd=str(tmp_path))
    assert not fires("cat build.py", cwd=str(tmp_path))
    assert not fires("echo done", cwd=str(tmp_path))


def test_silent_on_non_bash_tool(tmp_path):
    """⑦ Bash 가 아닌 도구는 침묵."""
    assert not fires("python3 build.py", tool_name="Write", cwd=str(tmp_path))


# ── 리마인더 내용 + fail-open ─────────────────────────────────────────

def test_reminder_mentions_shape_assertion(tmp_path):
    """⑧ 리마인더가 shape 어서션을 안내해야 (v4/v5 게이트)."""
    out = run_hook("python3 build_deck.py", cwd=str(tmp_path))
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "shape 어서션" in ctx
    assert "font.size" in ctx


def test_fail_open_on_bad_payload():
    """⑨ 입력 파싱 실패해도 rc 0 (세션 안 막음)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json at all",
        capture_output=True, text=True,
    )
    assert proc.returncode == 0


# ── H4: xlsx 신호 + 죽은 상수 제거 ────────────────────────────────────

def test_xlsx_engine_signal_triggers():
    # openpyxl 기반 xlsx 생성 명령이 리마인더를 발화해야 한다 (H4: xlsx 누락 수리)
    assert is_doc_build("python3 -c 'from openpyxl import Workbook; ...'")


def test_xlsx_named_script_triggers():
    # 빌더 권장 경로의 xlsx 스크립트 실행도 발화해야 한다
    assert is_doc_build("python3 build_xlsx_report.py")


def test_dead_doc_exts_removed():
    # H4: 죽은 상수가 다시 생기지 않도록 — 모듈에 DOC_EXTS가 없어야 한다
    assert not hasattr(mod, "DOC_EXTS")


# ── G1: verify-pending 센티널 arm/clear ───────────────────────────────

def test_arm_writes_slug_sentinel(tmp_path):
    """a) build 명령 + command에 outputs/mydeck/ 경로 포함 → .omd/mydeck/.verify-pending 생성."""
    (tmp_path / ".omd").mkdir()  # v0.5.1: arm requires an existing .omd/ project
    run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    sentinel = tmp_path / ".omd" / "mydeck" / ".verify-pending"
    assert sentinel.is_file()


def test_arm_writes_global_sentinel_when_slug_unknown(tmp_path):
    """b) build 명령 + slug 단서 없음 → .omd/.verify-pending 생성."""
    (tmp_path / ".omd").mkdir()
    run_hook("python3 build_deck.py", cwd=str(tmp_path))
    sentinel = tmp_path / ".omd" / ".verify-pending"
    assert sentinel.is_file()
    nested = tmp_path / ".omd" / "mydeck" / ".verify-pending"
    assert not nested.exists()


def test_clear_removes_all_sentinels_and_stays_silent(tmp_path):
    """c) pdftoppm 명령 → 기존 센티널 전부 제거, 리마인더 미발화."""
    (tmp_path / ".omd").mkdir()
    run_hook("python3 build_deck.py", cwd=str(tmp_path))
    run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    assert (tmp_path / ".omd" / ".verify-pending").is_file()
    assert (tmp_path / ".omd" / "mydeck" / ".verify-pending").is_file()

    out = run_hook("pdftoppm -png -r 150 deck.pdf out", cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / ".verify-pending").exists()
    assert not (tmp_path / ".omd" / "mydeck" / ".verify-pending").exists()


def test_clear_via_unzip_test_signal(tmp_path):
    (tmp_path / ".omd").mkdir()
    run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    sentinel = tmp_path / ".omd" / "mydeck" / ".verify-pending"
    assert sentinel.is_file()
    out = run_hook("unzip -t outputs/mydeck/deck.pptx", cwd=str(tmp_path))
    assert out.strip() == ""
    assert not sentinel.exists()


def test_sentinel_content_has_armed_at_and_command_head(tmp_path):
    """d) 센티널 내용은 json이고 armed_at(epoch float)·command_head(str) 키 보유."""
    (tmp_path / ".omd").mkdir()
    run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    sentinel = tmp_path / ".omd" / "mydeck" / ".verify-pending"
    data = json.loads(sentinel.read_text())
    assert isinstance(data["armed_at"], float)
    assert isinstance(data["command_head"], str)


def test_arm_fail_open_when_omd_uncreatable(tmp_path):
    """e) .omd 디렉토리 생성 불가(권한) 시에도 exit 0 (fail-open)."""
    blocker = tmp_path / ".omd"
    blocker.write_text("not a directory")
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 build_deck.py"},
            "cwd": str(tmp_path),
        }),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"


# ── HG-3: 리마인더 content-hash 쿨다운 ───────────────────────────────

def test_cooldown_suppresses_repeat_reminder_but_keeps_sentinel_arm(tmp_path):
    """f) 같은 build 명령 2회 연속 → 1회차 리마인더 발화 + throttle 파일 생성,
    2회차 출력 없음(단 센티널은 2회차에도 갱신 arm — 쿨다운은 메시지만 침묵)."""
    (tmp_path / ".omd").mkdir()
    out1 = run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    assert out1.strip() != ""
    throttle = tmp_path / ".omd" / ".hook-throttle.json"
    assert throttle.is_file()

    sentinel = tmp_path / ".omd" / "mydeck" / ".verify-pending"
    armed_at_1 = json.loads(sentinel.read_text())["armed_at"]

    out2 = run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    assert out2.strip() == ""
    armed_at_2 = json.loads(sentinel.read_text())["armed_at"]
    assert armed_at_2 >= armed_at_1


def test_cooldown_zero_disables_throttle(tmp_path):
    """g) OMD_REMINDER_COOLDOWN_SECONDS=0 이면 2회차도 발화 (쿨다운 해제)."""
    env = {"OMD_REMINDER_COOLDOWN_SECONDS": "0"}
    out1 = run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path), env=env)
    assert out1.strip() != ""
    out2 = run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path), env=env)
    assert out2.strip() != ""


def test_cooldown_fail_open_on_corrupt_throttle_file(tmp_path):
    """h) .omd/.hook-throttle.json이 깨진 JSON이어도 리마인더는 발화 (fail-open)."""
    omd = tmp_path / ".omd"
    omd.mkdir()
    (omd / ".hook-throttle.json").write_text("{not valid json")
    out = run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    assert out.strip() != ""


# ── D5 (R2): md 계열 Edit|Write 트리거 ────────────────────────────────
# md 산출물(repo-docs·site)은 Bash가 아니라 Edit|Write로 태어난다. 발화 조건 3중:
# .md 확장자 AND outputs/<slug>/ 경로 AND .omd/<slug>/ 실재(slug 컨텍스트 — §7 ②).
# 작업 메모(.omd/<slug>/*.md)는 deliverable이 아니므로 침묵(§7 ⑥ alert fatigue).

def run_md_hook(file_path: str, tool_name: str = "Edit", cwd: Optional[str] = None) -> str:
    payload = {"tool_name": tool_name, "tool_input": {"file_path": file_path}}
    if cwd is not None:
        payload["cwd"] = cwd
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return proc.stdout


def _with_slug(tmp_path, slug="2026-07-13-omd-readme"):
    (tmp_path / ".omd" / slug).mkdir(parents=True)
    return slug


def test_md_edit_fires_and_arms_on_single_file(tmp_path):
    """d1) 단일 파일 outputs/<slug>/current.md 편집 → 발화 + 센티널 arm."""
    slug = _with_slug(tmp_path)
    out = run_md_hook(f"outputs/{slug}/current.md", cwd=str(tmp_path))
    assert out.strip() != ""
    assert (tmp_path / ".omd" / slug / ".verify-pending").is_file()


def test_md_write_fires_on_artifact_set_member(tmp_path):
    """d2) artifact-set 멤버 Write → 발화."""
    slug = _with_slug(tmp_path)
    out = run_md_hook(f"outputs/{slug}/current/README.md", tool_name="Write", cwd=str(tmp_path))
    assert out.strip() != ""


def test_md_edit_fires_on_nested_site_tree(tmp_path):
    """d3) site 중첩 트리 픽스처(비평 #5 — 실물은 R3, 경로 구조는 지금 검증)."""
    slug = _with_slug(tmp_path)
    out = run_md_hook(f"outputs/{slug}/current/docs/how-to/deploy.md", cwd=str(tmp_path))
    assert out.strip() != ""
    assert (tmp_path / ".omd" / slug / ".verify-pending").is_file()


def test_md_edit_fires_on_absolute_path(tmp_path):
    """d4) 절대경로 file_path도 동일 판정 (textual segment 추출)."""
    slug = _with_slug(tmp_path)
    abs_path = str(tmp_path / "outputs" / slug / "current" / "README.md")
    assert run_md_hook(abs_path, cwd=str(tmp_path)).strip() != ""


def test_md_edit_silent_without_slug_context(tmp_path):
    """d5) .omd/<slug>/ 없으면 침묵 + 센티널 없음 (일반 md 편집 과발동 금지, §7 ②)."""
    out = run_md_hook("outputs/somedoc/current/README.md", cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / "somedoc" / ".verify-pending").exists()


def test_md_edit_silent_on_work_area_and_plain_paths(tmp_path):
    """d6) outputs/ 밖(.omd 작업 메모, 일반 docs/)은 slug 컨텍스트가 있어도 침묵."""
    slug = _with_slug(tmp_path)
    assert run_md_hook(f".omd/{slug}/build-notes.md", cwd=str(tmp_path)).strip() == ""
    assert run_md_hook("docs/notes.md", cwd=str(tmp_path)).strip() == ""


def test_non_md_write_silent(tmp_path):
    """d7) md가 아닌 파일 Write는 침묵."""
    slug = _with_slug(tmp_path)
    assert run_md_hook(f"outputs/{slug}/current/logo.png", tool_name="Write",
                       cwd=str(tmp_path)).strip() == ""


def test_md_reminder_points_at_card_gate(tmp_path):
    """d8) md 리마인더는 오피스 5/5가 아니라 카드 정의 verify gate를 가리켜야 (D1)."""
    slug = _with_slug(tmp_path)
    out = run_md_hook(f"outputs/{slug}/current/README.md", cwd=str(tmp_path))
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "verify gate" in ctx
    assert "repo-docs" in ctx
    assert "zip CRC" not in ctx  # 오피스 전용 문구 미혼입


def test_markdownlint_bash_clears_md_sentinel(tmp_path):
    """d9) markdownlint 실행(verify 신호)이 md-arm 센티널을 clear하고 침묵."""
    slug = _with_slug(tmp_path)
    run_md_hook(f"outputs/{slug}/current/README.md", cwd=str(tmp_path))
    sentinel = tmp_path / ".omd" / slug / ".verify-pending"
    assert sentinel.is_file()
    out = run_hook(f"npx markdownlint-cli2 outputs/{slug}/current/*.md", cwd=str(tmp_path))
    assert out.strip() == ""
    assert not sentinel.exists()


def test_md_edit_fail_open_on_missing_file_path(tmp_path):
    """d10) file_path 없는 payload도 rc 0·침묵 (fail-open)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": "Edit", "tool_input": {}, "cwd": str(tmp_path)}),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


# ── R3: mkdocs 신호 (결정 2 — verify-우선 매칭) ───────────────────────

def test_mkdocs_plain_build_arms_sentinel(tmp_path):
    """plain `mkdocs build` = 산출 빌드 → site 리마인더 + 센티널 arm."""
    slug = _with_slug(tmp_path)
    out = run_hook(
        f"uvx --from mkdocs --with mkdocs-material mkdocs build "
        f"-f outputs/{slug}/current/mkdocs.yml -d .omd/{slug}/site-build",
        cwd=str(tmp_path),
    )
    assert (tmp_path / ".omd" / slug / ".verify-pending").is_file()
    assert out.strip() != ""
    assert "--strict" in out     # 오피스 shape-assertion 문구가 아니라 site 카드 gate 안내


def test_mkdocs_strict_build_clears_sentinel(tmp_path):
    """`mkdocs build --strict` = 카드 gate ① verify 실행 → arm 아니라 clear (결정 2)."""
    slug = _with_slug(tmp_path)
    sentinel = tmp_path / ".omd" / slug / ".verify-pending"
    sentinel.write_text("{}")
    out = run_hook(
        f"uvx --from mkdocs --with mkdocs-material mkdocs build --strict "
        f"-f outputs/{slug}/current/mkdocs.yml -d .omd/{slug}/site-build",
        cwd=str(tmp_path),
    )
    assert not sentinel.exists(), "strict run must clear, not re-arm"
    assert out.strip() == ""     # verify 실행에 빌드 리마인더를 얹지 않음


def test_office_verify_signals_regression(tmp_path):
    """verify-우선 매칭 도입 후에도 기존 3신호(clear)·빌드신호(arm) 동작 무변."""
    slug = _with_slug(tmp_path)
    sentinel = tmp_path / ".omd" / slug / ".verify-pending"
    sentinel.write_text("{}")
    run_hook(f"pdftoppm -png outputs/{slug}/x.pdf p", cwd=str(tmp_path))
    assert not sentinel.exists()
    run_hook("python3 -c 'from pptx import Presentation'", cwd=str(tmp_path))
    assert (tmp_path / ".omd" / ".verify-pending").is_file()  # slug 무언급 → 루트 센티널


def test_md_reminder_names_site_gate(tmp_path, monkeypatch):
    """md Edit|Write 리마인더가 site 카드 gate 도 안내 (repo-docs 하드코딩 해소)."""
    monkeypatch.setenv("OMD_REMINDER_COOLDOWN_SECONDS", "0")
    slug = _with_slug(tmp_path)
    out = run_md_hook(f"outputs/{slug}/current/docs/index.md", cwd=str(tmp_path))
    assert "site" in out and "mkdocs build --strict" in out


# ── v0.5.1: 테스트 실행 오인·.omd 날조 회귀 고정 (2026-07-16 false-positive) ──

def test_pytest_run_with_doc_named_test_file_stays_silent(tmp_path):
    """pytest 대상 파일명에 'docs'가 있어도(빌드 아님) 침묵 + arm 없음 —
    2026-07-16 오탐 재현 커맨드 그대로."""
    (tmp_path / ".omd").mkdir()
    out = run_hook(
        "cd /root/oh-my-scholar && python3 -m pytest tests/test_scholar_verify_skill.py "
        "tests/test_wiki_spec_docs.py -q", cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / ".verify-pending").exists()


def test_directly_run_test_script_stays_silent(tmp_path):
    """python3 test_doc_render.py — 직접 실행이라도 test_* 스크립트는 빌드가 아님."""
    (tmp_path / ".omd").mkdir()
    out = run_hook("python3 test_doc_render.py", cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / ".verify-pending").exists()


def test_arm_never_fabricates_omd_root(tmp_path):
    """omd 프로젝트가 아닌 곳(.omd/ 부재)에서는 빌드 명령이라도 .omd/를 만들지 않는다.
    리마인더 자체는 발화(무결성 안내는 프로젝트 무관)."""
    out = run_hook("python3 build_deck.py", cwd=str(tmp_path))
    assert "document-integrity" in out
    assert not (tmp_path / ".omd").exists()


def test_hyphenated_pytest_like_build_script_still_arms(tmp_path):
    """'pytest'가 하이픈 파일명의 부분 문자열일 뿐이면 테스트 실행이 아니다 —
    진짜 빌드 스크립트는 여전히 arm (verifier finding 2026-07-16)."""
    (tmp_path / ".omd").mkdir()
    out = run_hook("python3 scripts/pytest-utils-report-deck.py output.pptx", cwd=str(tmp_path))
    assert "document-integrity" in out
    assert (tmp_path / ".omd" / ".verify-pending").is_file()
