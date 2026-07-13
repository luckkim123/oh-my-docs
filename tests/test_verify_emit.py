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

from hooks.docs_verify_emit import is_doc_build
import hooks.docs_verify_emit as mod

HOOK = Path(__file__).parent.parent / "hooks" / "docs_verify_emit.py"


def run_hook(command: str, tool_name: str = "Bash", cwd: str = None) -> str:
    """훅을 서브프로세스로 실행하고 stdout 반환 (fail-open: rc는 항상 0)."""
    payload = {"tool_name": tool_name, "tool_input": {"command": command}}
    if cwd is not None:
        payload["cwd"] = cwd
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return proc.stdout


def fires(command: str, tool_name: str = "Bash") -> bool:
    """리마인더가 주입됐는지 (stdout 비어있으면 침묵)."""
    return run_hook(command, tool_name=tool_name).strip() != ""


# ── 발동해야 하는 명령들 ──────────────────────────────────────────────

def test_fires_on_builder_recipe_script():
    """① 빌더 권장 경로 `python3 build.py` 발동 (옛 탐지 사각 — 2026-06-16 D6①)."""
    assert fires("python3 build.py")
    assert fires("python3 .omd/deck/build_deck.py")
    assert fires("python build_slides.py")
    assert fires("python3 make_presentation.py")


def test_fires_on_inline_engine_signal():
    """② 인라인 엔진 신호 발동 (-c 'from pptx ...' 회귀 방지)."""
    assert fires("python3 -c 'from pptx import Presentation'")


def test_fires_on_convert():
    """③ soffice 변환 발동."""
    assert fires("soffice --headless --convert-to pdf deck.pptx")


# ── 침묵해야 하는 명령들 (노이즈 제어) ────────────────────────────────

def test_silent_on_readonly_render():
    """④ read-only 렌더/무결성 검사는 침묵."""
    assert not fires("pdftoppm -png -r 150 deck.pdf slide")
    assert not fires("unzip -t deck.pptx")


def test_silent_on_unrelated_script():
    """⑤ 문서와 무관한 스크립트 실행은 침묵 (과발동 금지)."""
    assert not fires("python3 analyze_runs.py")
    assert not fires("python3 train.py")


def test_silent_on_non_exec():
    """⑥ 실행이 아닌 명령은 침묵."""
    assert not fires("ls *.py")
    assert not fires("cat build.py")
    assert not fires("echo done")


def test_silent_on_non_bash_tool():
    """⑦ Bash 가 아닌 도구는 침묵."""
    assert not fires("python3 build.py", tool_name="Write")


# ── 리마인더 내용 + fail-open ─────────────────────────────────────────

def test_reminder_mentions_shape_assertion():
    """⑧ 리마인더가 shape 어서션을 안내해야 (v4/v5 게이트)."""
    out = run_hook("python3 build_deck.py")
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
    run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    sentinel = tmp_path / ".omd" / "mydeck" / ".verify-pending"
    assert sentinel.is_file()


def test_arm_writes_global_sentinel_when_slug_unknown(tmp_path):
    """b) build 명령 + slug 단서 없음 → .omd/.verify-pending 생성."""
    run_hook("python3 build_deck.py", cwd=str(tmp_path))
    sentinel = tmp_path / ".omd" / ".verify-pending"
    assert sentinel.is_file()
    nested = tmp_path / ".omd" / "mydeck" / ".verify-pending"
    assert not nested.exists()


def test_clear_removes_all_sentinels_and_stays_silent(tmp_path):
    """c) pdftoppm 명령 → 기존 센티널 전부 제거, 리마인더 미발화."""
    run_hook("python3 build_deck.py", cwd=str(tmp_path))
    run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    assert (tmp_path / ".omd" / ".verify-pending").is_file()
    assert (tmp_path / ".omd" / "mydeck" / ".verify-pending").is_file()

    out = run_hook("pdftoppm -png -r 150 deck.pdf out", cwd=str(tmp_path))
    assert out.strip() == ""
    assert not (tmp_path / ".omd" / ".verify-pending").exists()
    assert not (tmp_path / ".omd" / "mydeck" / ".verify-pending").exists()


def test_clear_via_unzip_test_signal(tmp_path):
    run_hook("python3 outputs/mydeck/build_deck.py", cwd=str(tmp_path))
    sentinel = tmp_path / ".omd" / "mydeck" / ".verify-pending"
    assert sentinel.is_file()
    out = run_hook("unzip -t outputs/mydeck/deck.pptx", cwd=str(tmp_path))
    assert out.strip() == ""
    assert not sentinel.exists()


def test_sentinel_content_has_armed_at_and_command_head(tmp_path):
    """d) 센티널 내용은 json이고 armed_at(epoch float)·command_head(str) 키 보유."""
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
