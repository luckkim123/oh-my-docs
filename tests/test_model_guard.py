"""Tests for the model-tier advisory guard PreToolUse(Task) hook (docs_model_guard.py, G4).

핵심 계약: model 미지정은 정상 상태(spec AC-2) — 절대 경고하지 않는다. 감지 대상은
① 명시적으로 frontmatter와 다른 model을 지정한 호출 ② 존재하지 않는 oh-my-docs
subagent_type(오타). 둘 다 advisory 경고만 주입한다(D6: fail-open, block 없음).

isomorphic 출처: tests/test_verify_emit.py (같은 subprocess 패턴).
"""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent.parent / "hooks" / "docs_model_guard.py"


def _payload(subagent_type=None, model=None):
    ti = {}
    if subagent_type is not None:
        ti["subagent_type"] = subagent_type
    if model is not None:
        ti["model"] = model
    return {"tool_name": "Task", "tool_input": ti}


def run_hook(payload) -> str:
    """훅을 서브프로세스로 실행하고 stdout 반환 (fail-open: rc는 항상 0)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return proc.stdout


def fires(payload) -> bool:
    return run_hook(payload).strip() != ""


def test_mismatched_model_fires_and_names_both():
    """① 명시 model이 frontmatter와 불일치 → advisory 발화, 두 model 명시."""
    out = run_hook(_payload("oh-my-docs:doc-verifier", "haiku"))
    assert out.strip() != ""
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "opus" in ctx
    assert "haiku" in ctx


def test_matching_model_is_silent():
    """② 명시 model이 frontmatter와 일치 → 침묵."""
    assert not fires(_payload("oh-my-docs:doc-verifier", "opus"))


def test_unspecified_model_is_silent():
    """③ model 미지정 → 침묵 (미지정이 기본 상태 — spec AC-2)."""
    assert not fires(_payload("oh-my-docs:doc-builder"))


def test_unknown_agent_fires():
    """④ 존재하지 않는 oh-my-docs 에이전트(오타) → advisory."""
    out = run_hook(_payload("oh-my-docs:doc-bulder", None))
    assert out.strip() != ""
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "unknown" in ctx.lower()


def test_other_subagent_is_silent():
    """⑤ 타 플러그인/일반 subagent → 침묵."""
    assert not fires(_payload("general-purpose", "haiku"))


def test_fail_open_on_bad_payload():
    """⑥ 깨진 stdin(비JSON) → exit 0, 출력 없음 (fail-open)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json at all",
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""
