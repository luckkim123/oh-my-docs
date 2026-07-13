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


# ── HG-3: 리마인더 content-hash 쿨다운 ───────────────────────────────

def test_cooldown_suppresses_repeat_reminder_but_keeps_sentinel_arm(tmp_path):
    """f) 같은 build 명령 2회 연속 → 1회차 리마인더 발화 + throttle 파일 생성,
    2회차 출력 없음(단 센티널은 2회차에도 갱신 arm — 쿨다운은 메시지만 침묵)."""
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
