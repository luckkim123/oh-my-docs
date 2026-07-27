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
import time
from pathlib import Path
from typing import Optional

import pytest

import hooks.docs_verify_emit as mod
from hooks.docs_verify_emit import is_doc_build

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


def test_no_slug_context_arms_nothing_but_still_reminds(tmp_path):
    """b) v0.6.4 계약 역전: build 명령이라도 slug 단서가 없으면 센티널을 만들지
    않는다. 구계약(루트 센티널 무장)은 Stop 에서 "(slug unknown)" 이라 아무도
    조치할 수 없고 그 워크스페이스에서 clear 도 안 됐다. 리마인더 자체는 그대로
    발화하므로 "verify 하고 done 선언하라" 넛지는 유지된다."""
    (tmp_path / ".omd").mkdir()
    out = run_hook("python3 build_deck.py", cwd=str(tmp_path))
    assert "document-integrity" in out
    assert not (tmp_path / ".omd" / ".verify-pending").exists()
    assert not (tmp_path / ".omd" / "mydeck" / ".verify-pending").exists()


def test_clear_removes_all_sentinels_and_stays_silent(tmp_path):
    """c) pdftoppm 명령 → 기존 센티널 전부 제거, 리마인더 미발화. 루트 센티널은
    v0.6.4 이후 무장되지 않으므로 구버전 잔재를 직접 심어 광역 clear 계약을
    그대로 검증한다."""
    (tmp_path / ".omd").mkdir()
    (tmp_path / ".omd" / ".verify-pending").write_text(
        json.dumps({"armed_at": time.time(), "command_head": "legacy"}))
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
            "tool_input": {"command": "python3 outputs/mydeck/build_deck.py"},
            "cwd": str(tmp_path),
        }),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                     reason="chmod cannot block root")
def test_arm_write_failure_still_fires_reminder_no_half_sentinel(tmp_path):
    """e2) arm_sentinel()'s own write failing (mkstemp/replace error, e.g. disk
    full or permission) must fail open — the build reminder still fires
    (main()'s except around arm_sentinel, lines 294-295) AND no half-written
    sentinel is left behind for the Stop guard to trip over."""
    omd = tmp_path / ".omd"
    omd.mkdir()
    os.chmod(omd, 0o555)  # read+exec only: mkstemp() cannot create a tmp file here
    try:
        # slug 있는 명령이어야 arm 이 실제로 시도된다 (v0.6.4: slug 없으면 애초에
        # 쓰지 않으므로 쓰기 실패 경로를 못 탄다 — 테스트가 공허해짐).
        out = run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    finally:
        os.chmod(omd, 0o755)
    assert "document-integrity" in out
    assert not (omd / "mydeck" / ".verify-pending").exists()


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
    run_hook("python3 -c 'from pptx import Presentation'",
             cwd=str(tmp_path / ".omd" / slug))
    assert sentinel.is_file()  # 빌드 신호는 여전히 arm (slug 는 cwd 에서 유도, D1)


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
    slug = _with_slug(tmp_path, "mydeck")
    out = run_hook("python3 outputs/mydeck/scripts/pytest-utils-report-deck.py out.pptx",
                   cwd=str(tmp_path))
    assert "document-integrity" in out
    assert (tmp_path / ".omd" / slug / ".verify-pending").is_file()


# Recovered verbatim from vault session 4f56a5f0 (2026-07-15): a robotics
# deploy+test pipeline whose `python3 -m pytest ... test_obs_builder.py` segment
# matched RUN_SCRIPT_RE via the "build" substring of "obs_builder" and planted a
# never-cleared slugless sentinel in a workspace with no document history.
# Distinct from the oh-my-scholar incident above: multi-line compound command,
# ssh + docker exec wrapping, and a doc keyword hit inside a NON-test-prefixed
# word ("obs_builder") — only the standalone pytest token saves it.
VAULT_INCIDENT_CMD = """cat /Users/<you>/.claude/jobs/<id>/tmp/frames_new.py | ssh <remote-host> "docker exec -i <container> bash -c 'cat > /workspace/src/<sim_pkg>/<bridge_pkg>/<bridge_pkg>/frames.py'" 2>/dev/null
cat /Users/<you>/.claude/jobs/<id>/tmp/test_frames_new.py | ssh <remote-host> "docker exec -i <container> bash -c 'cat > /workspace/src/<sim_pkg>/<bridge_pkg>/test/test_frames.py'" 2>/dev/null
ssh <remote-host> 'docker exec <container> bash -lc "source /opt/ros/humble/setup.bash; source /workspace/install/setup.bash 2>/dev/null; cd /workspace && colcon build --packages-select <bridge_pkg> --merge-install >/tmp/build.log 2>&1 && echo BUILD_OK || (echo BUILD_FAIL; tail -15 /tmp/build.log); source install/setup.bash; echo ===TESTS===; python3 -m pytest src/<sim_pkg>/<bridge_pkg>/test/test_frames.py src/<sim_pkg>/<bridge_pkg>/test/test_obs_builder.py -q 2>&1 | tail -20"' 2>&1 | grep -v -iE 'tailscale|attest|node key'"""


def test_remote_deploy_pytest_pipeline_stays_silent(tmp_path):
    """2026-07-15 vault incident verbatim: remote pytest over a *_builder.py test
    file is not a doc build — silent, nothing armed."""
    assert not is_doc_build(VAULT_INCIDENT_CMD)
    (tmp_path / ".omd").mkdir()
    out = run_hook(VAULT_INCIDENT_CMD, cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / ".verify-pending").exists()


# ── D1 (v0.6.2): cwd 기반 root/slug 유도 (2026-07-21 utracker-seminar 누수) ──
# verify 신호(pdftoppm 등)를 .omd/<slug>/ 하위 cwd 에서 상대경로로 실행하면
# ① 명령 문자열에 slug 가 없고(SLUG_RE 미스) ② root 해석(<cwd>/.omd)마저
# 존재하지 않는 경로가 되어 clear_sentinels 가 isdir 가드에서 조기 반환 —
# 진짜 slug 센티널이 살아남아 Stop 가드가 세션 내내 재경고했다. 수정: 명령에
# slug 단서가 없으면 cwd 경로 성분(.omd/<slug>/ 또는 outputs/<slug>/ 앵커)에서
# 프로젝트 .omd root 와 slug 를 유도한다. cwd 로 slug 를 특정한 clear 는 그
# slug 만 지운다(광범위 clear 로 가드 무력화 금지 — 사용자 명시 제약).
# slug 단서가 어디에도 없으면 기존 광역 폴백 그대로 (동작 무변 —
# test_clear_removes_all_sentinels_and_stays_silent 가 그 계약을 잠근다).


def _plant_sentinel(tmp_path, slug):
    d = tmp_path / ".omd" / slug
    d.mkdir(parents=True, exist_ok=True)
    s = d / ".verify-pending"
    s.write_text(json.dumps({"armed_at": time.time(),
                             "command_head": "python3 build_deck.py"}))
    return s


def test_clear_from_inside_slug_dir_relative_render(tmp_path):
    """D1a) verify 신호를 .omd/<slug>/ 하위 cwd 에서 상대경로로 실행해도 그
    slug 센티널이 지워진다 — 2026-07-21 사고 재현 형태(렌더 하위 디렉토리)."""
    sentinel = _plant_sentinel(tmp_path, "utracker-seminar")
    renders = tmp_path / ".omd" / "utracker-seminar" / "renders"
    renders.mkdir()
    out = run_hook("pdftoppm -png -r 150 deck.pdf page", cwd=str(renders))
    assert out.strip() == ""
    assert not sentinel.exists()


def test_clear_from_slug_cwd_touches_only_that_slug(tmp_path):
    """D1b) cwd 로 slug 를 특정한 clear 는 그 slug 만 — 다른 slug·루트 센티널은
    남는다."""
    target = _plant_sentinel(tmp_path, "mydeck")
    other = _plant_sentinel(tmp_path, "otherdeck")
    root_sentinel = tmp_path / ".omd" / ".verify-pending"
    root_sentinel.write_text(json.dumps({"armed_at": time.time(), "command_head": "x"}))
    run_hook("unzip -t deck.pptx", cwd=str(tmp_path / ".omd" / "mydeck"))
    assert not target.exists()
    assert other.is_file()
    assert root_sentinel.is_file()


def test_clear_from_outputs_slug_cwd(tmp_path):
    """D1c) outputs/<slug>/ 하위 cwd 도 동일 유도 (SLUG_RE 앵커와 대칭)."""
    sentinel = _plant_sentinel(tmp_path, "mydeck")
    workdir = tmp_path / "outputs" / "mydeck" / "current"
    workdir.mkdir(parents=True)
    out = run_hook("pdftoppm -png deck.pdf p", cwd=str(workdir))
    assert out.strip() == ""
    assert not sentinel.exists()


def test_arm_from_inside_slug_dir_arms_that_slug(tmp_path):
    """D1d) 빌드를 .omd/<slug>/ 안에서 돌려도 그 slug 로 arm 된다 (전에는 root
    미존재로 무장 자체가 조용히 누락 — 같은 결함 계열의 arm 쪽 증상)."""
    slug_dir = tmp_path / ".omd" / "mydeck"
    slug_dir.mkdir(parents=True)
    run_hook("python3 build_deck.py", cwd=str(slug_dir))
    assert (slug_dir / ".verify-pending").is_file()
    assert not (tmp_path / ".omd" / ".verify-pending").exists()


# ── v0.6.3: read-only/inspection commands must not arm (2026-07-24 false positive) ──
# A slugless .verify-pending was armed in a workspace that built NOTHING, by
# commands that merely NAMED an engine string: (a) a grep whose search PATTERN
# listed engine strings while investigating the hooks, (b) an openpyxl
# load-and-print dump of an xlsx template (the live incident: cd; cp a template
# from a volume; python3 -c 'load_workbook + print'). Neither generates a
# document, yet both matched a BUILD_SIGNAL substring and armed the root
# sentinel, so the Stop guard re-warned "(slug unknown)" all session. Same "an
# engine string named as data is not a build" narrowing as TEST_RUN_RE (v0.5.1).

def test_silent_on_grep_for_engine_strings(tmp_path):
    """a) grep whose pattern lists engine strings is investigation, not a build."""
    (tmp_path / ".omd").mkdir()
    cmd = "grep -rE 'openpyxl|Presentation|soffice|--convert-to' hooks/"
    assert not is_doc_build(cmd)
    out = run_hook(cmd, cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / ".verify-pending").exists()


def test_silent_on_rg_for_engine_strings(tmp_path):
    """a2) ripgrep is the same shape — a leading read-only viewer."""
    (tmp_path / ".omd").mkdir()
    assert not is_doc_build("rg 'from pptx import Presentation' hooks/")
    assert run_hook("cat hooks/docs_verify_emit.py", cwd=str(tmp_path)).strip() == ""


def test_silent_on_readonly_openpyxl_dump(tmp_path):
    """b) openpyxl load_workbook + print (no write) dumps a template — not a build."""
    (tmp_path / ".omd").mkdir()
    cmd = ("python3 -c 'from openpyxl import load_workbook; "
           "wb=load_workbook(\"template.xlsx\"); print(wb.active.max_row)'")
    assert not is_doc_build(cmd)
    out = run_hook(cmd, cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / ".verify-pending").exists()


def test_silent_on_live_incident_compound(tmp_path):
    """b2) 2026-07-24 live incident shape verbatim: cd; cp a template from a
    volume; then dump its cells read-only. A compound `cp` command whose only
    engine mention is a read-only openpyxl dump must not arm."""
    (tmp_path / ".omd").mkdir()
    cmd = ('cd "/tmp/work"\n'
           '# 템플릿 재확보(cwd 리셋 대비)\n'
           'cp "/Volumes/ext/herolab-master.xlsx" .\n'
           "python3 -c 'from openpyxl import load_workbook; "
           "wb=load_workbook(\"herolab-master.xlsx\"); "
           "print([c.value for c in wb.active[1]])'")
    assert not is_doc_build(cmd)
    out = run_hook(cmd, cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / ".verify-pending").exists()


def test_openpyxl_edit_and_save_still_builds():
    """c) a genuine xlsx edit (load_workbook ... .save) IS a build — the write
    indicator (.save) distinguishes it from a read-only dump. Regression guard."""
    assert is_doc_build(
        "python3 -c 'from openpyxl import load_workbook; "
        "wb=load_workbook(\"t.xlsx\"); wb.save(\"out.xlsx\")'")


def test_new_workbook_still_builds():
    """c2) constructing a new Workbook is unquestionably a build (pinned by
    test_xlsx_engine_signal_triggers too — restated here beside the narrowing)."""
    assert is_doc_build("python3 -c 'from openpyxl import Workbook; wb=Workbook()'")


def test_real_build_piping_to_tail_still_arms(tmp_path):
    """c3) the narrowing keys on the LEADING command, so a real build that pipes
    its log through tail/grep is untouched (leading token is python3, not a
    read-only viewer)."""
    (tmp_path / ".omd").mkdir()
    out = run_hook("python3 outputs/mydeck/build_deck.py 2>&1 | tail -5",
                   cwd=str(tmp_path))
    assert (tmp_path / ".omd" / "mydeck" / ".verify-pending").is_file()
    assert out.strip() != ""


# ── v0.6.3 code-review findings (2026-07-24 adversarial review) ──────────────

def test_readonly_lead_re_is_not_redos():
    """HIGH: READONLY_LEAD_RE must not catastrophically backtrack — a leading
    `cd a && `×N chain plus a trailing engine string used to hang is_doc_build
    (~6s at 200 chars). main() runs is_doc_build outside try/except, so a hang
    freezes the turn. The DIR class excludes space to keep matching linear."""
    import time as _t
    # A leading `cd`-chain with NO viewer at the end is the worst case: the regex
    # must scan the whole chain and then FAIL to find a viewer. The old class
    # (space-inclusive) explored every chain partition on that failure (~6s @ 200
    # chars); the fix keeps the failing scan linear. The boolean result is
    # immaterial here (it is True — a bare engine token is not a read-only
    # inspection); the ReDoS property is purely latency.
    cmd = "cd a && " * 40 + "openpyxl"      # 328 chars — old regex: many seconds
    start = _t.perf_counter()
    is_doc_build(cmd)
    elapsed = _t.perf_counter() - start
    assert elapsed < 0.5, f"is_doc_build took {elapsed:.3f}s — backtracking regression"


def test_silent_on_head_tail_git_grep_inspection(tmp_path):
    """MEDIUM: the natural investigation prefixes named in the fix (head/tail,
    git grep) must not arm — these directly recur the incident this PR targets."""
    (tmp_path / ".omd").mkdir()
    for cmd in (
        "head -50 render_openpyxl.py",
        "tail -20 build_deck.log",
        "git grep -n 'from pptx import Presentation'",
        "cd hooks && grep -rE 'openpyxl|--convert-to' .",
    ):
        assert not is_doc_build(cmd), cmd
        assert run_hook(cmd, cwd=str(tmp_path)).strip() == "", cmd
    assert not (tmp_path / ".omd" / ".verify-pending").exists()


def test_openpyxl_save_with_space_still_builds():
    """LOW: `.save (` spacing is still a write — XLSX_WRITE_RE tolerates the
    space so a genuine save is not silenced as a read-only dump."""
    assert is_doc_build(
        "python3 -c 'from openpyxl import load_workbook; "
        "wb=load_workbook(\"t.xlsx\"); wb.save (\"o.xlsx\")'")


# ── v0.6.4: a VERIFY render must not arm the sentinel it verifies (cause A) ──
# 2026-07-27 incident, recovered verbatim from session transcript 3230a10e
# (ts 2026-07-24T07:44:47Z): a docx integrity check rendered the file to PDF in
# $CLAUDE_JOB_DIR/tmp to count pages — the card's own "fresh render evidence"
# step. `--convert-to` matched BUILD_SIGNALS, is_verify_run did not match, so
# the verify step ARMED verify-pending. Note the trailing echo also names
# `python-docx`, so narrowing only the convert-family signal is not enough —
# the whole signal route must yield to the inspection verdict.
SOFFICE_VERIFY_RENDER_CMD = """DOCX="/Users/<you>/workspace/91_Inbox/(2026.07.24)product.docx"
OUTDIR="$CLAUDE_JOB_DIR/tmp/render"
mkdir -p "$OUTDIR"
SOFFICE=""
for c in soffice /Applications/LibreOffice.app/Contents/MacOS/soffice libreoffice; do \
  command -v "$c" >/dev/null 2>&1 && SOFFICE="$c" && break; done
if [ -n "$SOFFICE" ]; then
  "$SOFFICE" --headless --convert-to pdf --outdir "$OUTDIR" "$DOCX" >/dev/null 2>&1
  PDF=$(ls "$OUTDIR"/*.pdf 2>/dev/null | head -1)
  echo "RENDER OK -> $PDF pages=$(pdfinfo "$PDF" | awk '/Pages/{print $2}')"
else
  echo "soffice not found — skipping render (zip CRC + python-docx parse already passed)"
fi"""


def test_verify_render_to_scratch_outdir_does_not_arm(tmp_path):
    """A1) 사고 명령 원문: 스크래치 --outdir 로의 변환은 검증 렌더 → 무장 금지."""
    slug = _with_slug(tmp_path, "mydeck")
    assert not is_doc_build(SOFFICE_VERIFY_RENDER_CMD)
    out = run_hook(SOFFICE_VERIFY_RENDER_CMD, cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / ".verify-pending").exists()
    assert not (tmp_path / ".omd" / slug / ".verify-pending").exists()


def test_verify_render_inside_slug_context_does_not_rearm(tmp_path):
    """A2) slug 컨텍스트가 있어도 마찬가지 — 검증 직후 "미검증" 경고가 뜨는
    역전이 원인 B 와 독립적으로 남아 있으면 안 된다."""
    slug = _with_slug(tmp_path, "utracker-seminar")
    cmd = (f"soffice --headless --convert-to pdf --outdir /tmp/omd-render "
           f"outputs/{slug}/current.pptx")
    assert not is_doc_build(cmd)
    assert run_hook(cmd, cwd=str(tmp_path)).strip() == ""
    assert not (tmp_path / ".omd" / slug / ".verify-pending").exists()


def test_delivery_convert_into_outputs_still_arms(tmp_path):
    """A3) 회귀: 납품 변환(카드 규칙 = outputs/<slug>/ 로 쓴다)은 여전히 빌드."""
    slug = _with_slug(tmp_path, "mydeck")
    cmd = (f"soffice --headless --convert-to pdf --outdir outputs/{slug}/ "
           f"outputs/{slug}/current.pptx")
    assert is_doc_build(cmd)
    run_hook(cmd, cwd=str(tmp_path))
    assert (tmp_path / ".omd" / slug / ".verify-pending").is_file()


def test_convert_without_outdir_still_arms(tmp_path):
    """A4) 회귀: --outdir 자체가 없으면 소스 옆에 쓰므로 빌드 판정 유지."""
    assert is_doc_build("soffice --headless --convert-to pdf deck.pptx")


def test_scratch_render_still_arms_when_a_doc_script_runs(tmp_path):
    """A5) 스크래치 렌더가 붙어 있어도 doc-네임 스크립트 실행은 빌드다
    (v0.6.3 이 세운 '스크립트 경로는 무효화되지 않는다' 계약 유지)."""
    slug = _with_slug(tmp_path, "mydeck")
    cmd = (f"python3 outputs/{slug}/build_deck.py && "
           f"soffice --convert-to pdf --outdir /tmp/r outputs/{slug}/current.pptx")
    assert is_doc_build(cmd)
    run_hook(cmd, cwd=str(tmp_path))
    assert (tmp_path / ".omd" / slug / ".verify-pending").is_file()


def test_outdir_variable_is_resolved_not_taken_literally():
    """A6) `--outdir "$OUTDIR"` 는 변수명이 아니라 담긴 경로로 판정해야 한다 —
    사고 명령이 실제로 쓰는 형태."""
    scratch = """OUT="$CLAUDE_JOB_DIR/tmp"
soffice --convert-to pdf --outdir "$OUT" a.docx"""
    delivery = """OUT="outputs/mydeck"
soffice --convert-to pdf --outdir "$OUT" a.docx"""
    assert not is_doc_build(scratch)
    assert is_doc_build(delivery)


# ── v0.6.4: slug 컨텍스트 없는 무장 금지 (cause B) ───────────────────────────

def test_vault_incident_class_cannot_arm_even_if_misclassified(tmp_path):
    """B1) G7 이 막으려던 원래 사고(2026-07-15 vault): 오분류된 명령이 문서 이력
    없는 워크스페이스에 영구 센티널을 심었다. 이제는 오분류되더라도 slug 가
    없으므로 심을 곳이 없다 — TTL(G7) 없이도 구조적으로 불가능."""
    (tmp_path / ".omd").mkdir()
    # 일부러 빌드로 분류되는 slug 없는 명령 (분류 자체는 True)
    assert is_doc_build("python3 -c 'from pptx import Presentation; Presentation()'")
    run_hook("python3 -c 'from pptx import Presentation; Presentation()'",
             cwd=str(tmp_path))
    assert list((tmp_path / ".omd").glob("**/.verify-pending")) == []


def test_slug_from_cwd_still_arms(tmp_path):
    """B2) 회귀: slug 를 cwd 에서 유도할 수 있으면 여전히 무장한다 (D1 계약)."""
    slug_dir = tmp_path / ".omd" / "mydeck"
    slug_dir.mkdir(parents=True)
    run_hook("python3 build_deck.py", cwd=str(slug_dir))
    assert (slug_dir / ".verify-pending").is_file()


# ── v0.6.4: 센티널이 스스로를 설명한다 (부수결함 2) ──────────────────────────

def test_sentinel_records_matching_signal(tmp_path):
    """마커에 어떤 규칙이 무장시켰는지 기록 — 원인 규명에 세션 전사 발굴이
    필요했던 2026-07-27 진단 불능 해소."""
    slug = _with_slug(tmp_path, "mydeck")
    run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    data = json.loads((tmp_path / ".omd" / slug / ".verify-pending").read_text())
    assert data["signal"] == "script:build_deck.py"

    (tmp_path / ".omd" / slug / ".verify-pending").unlink()
    run_hook("python3 -c 'from pptx import Presentation'",
             cwd=str(tmp_path / ".omd" / slug))
    data = json.loads((tmp_path / ".omd" / slug / ".verify-pending").read_text())
    assert data["signal"] == "signal:from pptx"


def test_command_head_survives_a_long_absolute_path(tmp_path):
    """head 80자가 절대경로 하나로 소진돼 진단이 불가능했다 — 200자로."""
    slug = _with_slug(tmp_path, "mydeck")
    long_path = "/Users/x/" + "verylongdirectoryname/" * 5
    run_hook(f"python3 outputs/mydeck/build_deck.py {long_path}deck.pptx",
             cwd=str(tmp_path))
    data = json.loads((tmp_path / ".omd" / slug / ".verify-pending").read_text())
    assert len(data["command_head"]) > 80


# ── C (v0.6.5): 명령 안의 `cd` 가 훅에 보이지 않는다 (2026-07-27 두 번째 사고) ──
# PostToolUse 페이로드의 cwd 는 *세션* cwd 다. 명령이 `cd <other-repo> && …` 로
# 다른 저장소에 들어가 거기서만 작업해도, 훅은 세션 cwd 기준으로 root 를 잡아
# **이 워크스페이스**의 .omd/ 에 센티널을 떨어뜨린다. 실제 사고: omd 훅 자체를
# 조사하려고 oh-my-docs/hooks 로 cd 해서 돌린 힙독이, 무관한 워크스페이스의
# .omd/utracker-seminar/ 를 "미검증"으로 낙인찍었다 (v0.6.4 로도 재현됨 —
# v0.6.4 의 "slug 없으면 arm 안 함"은 slug 가 *문자열로 언급*되면 통과한다).

HOOK_PROBE_CMD_TMPL = (
    "cd {target} && python3 - <<'PY'\n"
    "import docs_verify_emit as m\n"
    'print(m.is_doc_build("soffice --headless --convert-to pdf x.docx"))\n'
    'print(m._slug_of(".omd/utracker-seminar/build/deck.py", ""))\n'
    "PY"
)


def _workspace_with_slug(tmp_path, slug="utracker-seminar"):
    d = tmp_path / "workspace" / ".omd" / slug
    d.mkdir(parents=True)
    return tmp_path / "workspace", d / ".verify-pending"


def test_cd_into_other_repo_arms_nothing_in_this_workspace(tmp_path):
    """C) `cd <다른 repo>` 로 시작하는 명령은 이 워크스페이스의 센티널을 건드리지
    않는다 — 2026-07-27 사고 재현본. 그 repo 엔 .omd 가 없으니 아무데도 안 무장."""
    workspace, sentinel = _workspace_with_slug(tmp_path)
    other = tmp_path / "oh-my-docs" / "hooks"
    other.mkdir(parents=True)
    run_hook(HOOK_PROBE_CMD_TMPL.format(target=other), cwd=str(workspace))
    assert not sentinel.exists(), "다른 repo 로 cd 한 명령이 이 워크스페이스를 오염시킴"


def test_same_command_without_cd_still_arms(tmp_path):
    """C-대조군) 같은 명령이라도 `cd` 없이 이 워크스페이스에서 돌면 그대로 무장한다
    — 수정이 '전부 침묵'이 아니라 *어디서 돌았나*를 본다는 증거."""
    workspace, sentinel = _workspace_with_slug(tmp_path)
    body = HOOK_PROBE_CMD_TMPL.format(target="X").split("&&", 1)[1].lstrip()
    run_hook(body, cwd=str(workspace))
    assert sentinel.is_file()


def test_cd_into_this_workspace_still_arms(tmp_path):
    """C-회귀) 워크스페이스 안으로 cd 하는 정상 빌드는 계속 무장한다."""
    workspace, _ = _workspace_with_slug(tmp_path, "mydeck")
    sentinel = workspace / ".omd" / "mydeck" / ".verify-pending"
    run_hook(f"cd {workspace} && python3 .omd/mydeck/build_deck.py", cwd=str(workspace))
    assert sentinel.is_file()


def test_relative_cd_resolves_against_session_cwd(tmp_path):
    """C-상대경로) `cd sub && …` 는 세션 cwd 기준으로 해석한다."""
    workspace, _ = _workspace_with_slug(tmp_path, "mydeck")
    (workspace / "sub").mkdir()
    run_hook("cd sub && python3 .omd/mydeck/build_deck.py", cwd=str(workspace))
    assert not (workspace / "sub" / ".omd").exists(), "없는 root 를 날조하면 안 됨"
    assert not (workspace / ".omd" / "mydeck" / ".verify-pending").exists()


def test_cd_lead_re_is_not_redos():
    """CD_LEAD_RE 도 같은 규율을 지킨다 — 앵커 1회 매치, 바깥 반복 없음, 세 분기의
    구분자 집합이 disjoint. 최악 케이스는 닫히지 않은 따옴표(첫 분기가 끝까지 훑고
    실패한 뒤 나머지 분기로 넘어감)."""
    import time as _t
    for cmd in ('cd "' + "a" * 4000,
                "cd " + "a" * 4000,
                "cd " + "a/" * 2000 + " && python3 build.py"):
        start = _t.perf_counter()
        mod._command_cwd(cmd, "/tmp")
        elapsed = _t.perf_counter() - start
        assert elapsed < 0.5, f"_command_cwd took {elapsed:.3f}s — backtracking regression"
