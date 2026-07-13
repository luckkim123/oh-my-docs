"""Tests for the advisory Stop-guard hook (docs_stop_guard.py, G1).

핵심 계약: docs_verify_emit이 arm한 `.omd/**/.verify-pending` 센티널이 Stop
시점까지 남아있으면 advisory 리마인드를 낸다 — decision:block은 절대 금지(D6),
verify를 나중에 해도 무방하다는 문구가 필수(HK-2). stop_hook_active 재진입
가드(G1-chk), 6시간 이상 묵은 센티널은 "carried over"로 구분 표시(HK-4).
stdlib only, fail-open.

isomorphic 출처: tests/test_verify_emit.py (같은 subprocess 패턴, tmp_path를
payload cwd로 주입)."""
import json
import subprocess
import sys
import time
from pathlib import Path

HOOK = Path(__file__).parent.parent / "hooks" / "docs_stop_guard.py"


def run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )


def write_sentinel(root: Path, slug: str, armed_at: float) -> Path:
    d = root / slug if slug else root
    d.mkdir(parents=True, exist_ok=True)
    path = d / ".verify-pending"
    path.write_text(json.dumps({"armed_at": armed_at, "command_head": "python3 build_deck.py"}))
    return path


def test_no_sentinels_silent(tmp_path):
    """1) 센티널 0개 → 출력 없음, exit 0."""
    proc = run_hook({"cwd": str(tmp_path)})
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_pending_sentinel_advisory_reminder(tmp_path):
    """2) .omd/mydeck/.verify-pending 존재 → "mydeck"과 "advisory" 포함, "decision" 키 부재."""
    root = tmp_path / ".omd"
    write_sentinel(root, "mydeck", time.time())
    proc = run_hook({"cwd": str(tmp_path)})
    assert proc.returncode == 0
    assert proc.stdout.strip() != ""
    d = json.loads(proc.stdout)
    assert "decision" not in d
    combined = json.dumps(d)
    assert "mydeck" in combined
    assert "advisory" in combined


def test_stop_hook_active_reentry_guard(tmp_path):
    """3) payload {"stop_hook_active": true} → 센티널 있어도 출력 없음 (재진입 가드)."""
    root = tmp_path / ".omd"
    write_sentinel(root, "mydeck", time.time())
    proc = run_hook({"cwd": str(tmp_path), "stop_hook_active": True})
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_stale_sentinel_marked_carried_over(tmp_path):
    """4) armed_at이 7시간 전인 센티널 → 출력에 "carried over" 포함."""
    root = tmp_path / ".omd"
    write_sentinel(root, "olddeck", time.time() - 7 * 3600)
    proc = run_hook({"cwd": str(tmp_path)})
    assert proc.returncode == 0
    assert "carried over" in proc.stdout


def test_fail_open_on_broken_stdin():
    """5) 깨진 stdin → exit 0 (fail-open)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json at all",
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
