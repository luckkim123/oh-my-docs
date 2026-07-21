"""Tests for the advisory Stop-guard hook (docs_stop_guard.py, G1).

핵심 계약: docs_verify_emit이 arm한 `.omd/**/.verify-pending` 센티널이 Stop
시점까지 남아있으면 advisory 리마인드를 낸다 — decision:block은 절대 금지(D6),
verify를 나중에 해도 무방하다는 문구가 필수(HK-2). stop_hook_active 재진입
가드(G1-chk), 6시간 이상 묵은 센티널은 "carried over"로 구분 표시(HK-4).
stdlib only, fail-open.

isomorphic 출처: tests/test_verify_emit.py (같은 subprocess 패턴, tmp_path를
payload cwd로 주입).

G5 추가: docs-pilot이 각 스테이지 dispatch/skip 시 `.omd/<slug>/stage-evidence.log`에
남기는 마커(`OMD stage <n> <name> → spawned|skipped: ...`)를 grep해 1..6 누락을
advisory로 보고한다. mtime이 STALE_AFTER(6h)를 넘은 로그는 HK-4의 named exception —
끝난 실행의 감사 기록일 뿐 미해결 작업이 아니므로 무시한다."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from hooks.docs_stop_guard import expire_stale_slugless

HOOK = Path(__file__).parent.parent / "hooks" / "docs_stop_guard.py"


def run_hook(payload: dict, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    run_env = {**os.environ, **env} if env else None
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True,
        env=run_env,
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


def write_evidence(root: Path, slug: str, lines, old: bool = False) -> Path:
    d = root / slug if slug else root
    d.mkdir(parents=True, exist_ok=True)
    path = d / "stage-evidence.log"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if old:
        past = time.time() - 8 * 3600
        os.utime(path, (past, past))
    return path


def test_stage_evidence_gap_reported(tmp_path):
    """6) G5: recent pilot log missing stage markers -> advisory names the gaps."""
    root = tmp_path / ".omd"
    write_evidence(root, "deck", [
        "OMD stage 1 intake → spawned oh-my-docs:doc-analyzer",
        "OMD stage 2 standardize → skipped: no reference documents",
        "OMD stage 4 build → spawned oh-my-docs:doc-builder",
    ])
    proc = run_hook({"cwd": str(tmp_path)})
    assert proc.returncode == 0
    assert "stage-evidence" in proc.stdout
    for missing in ("3", "5", "6"):
        assert missing in proc.stdout


def test_stage_evidence_complete_is_silent(tmp_path):
    """7) all 6 stage markers present -> no advisory."""
    root = tmp_path / ".omd"
    write_evidence(root, "deck", [
        f"OMD stage {n} x → spawned oh-my-docs:doc-x" for n in range(1, 7)])
    proc = run_hook({"cwd": str(tmp_path)})
    assert proc.returncode == 0
    assert "stage-evidence" not in proc.stdout


def test_stage_evidence_old_log_ignored(tmp_path):
    """8) PD-3: an old log (mtime > STALE_AFTER) is a finished run's audit
    trail, not unresolved work — the named HK-4 exception."""
    root = tmp_path / ".omd"
    write_evidence(root, "deck", ["OMD stage 1 intake → spawned x"], old=True)
    proc = run_hook({"cwd": str(tmp_path)})
    assert proc.returncode == 0
    assert "stage-evidence" not in proc.stdout


# ── G7: slugless sentinel self-expiry (2026-07-15 vault incident) ────────────
# A slugless root sentinel names no .omd/<slug>/ workspace, so in a workspace
# that never runs verify signals nothing ever clears it — without a TTL the
# guard repeats "(slug unknown)" at every Stop forever. Slugged sentinels mark
# real carried-over work (HK-4) and must never expire.

def test_slugless_sentinel_expires_after_ttl(tmp_path):
    """9) G7: a slugless root sentinel older than SLUGLESS_EXPIRE_AFTER is
    removed with one final notice; the following Stop is silent."""
    root = tmp_path / ".omd"
    write_sentinel(root, "", time.time() - 8 * 24 * 3600)
    proc = run_hook({"cwd": str(tmp_path)})
    assert proc.returncode == 0
    message = json.loads(proc.stdout)["systemMessage"]  # stdout is \u-escaped JSON
    assert "만료" in message
    assert "(slug unknown)" not in message
    assert not (root / ".verify-pending").exists()
    proc2 = run_hook({"cwd": str(tmp_path)})
    assert proc2.returncode == 0
    assert proc2.stdout.strip() == ""


def test_slugless_sentinel_fresh_keeps_normal_advisory(tmp_path):
    """10) a slugless sentinel younger than the TTL keeps the normal advisory
    (stale-tagged after 6h, but not expired)."""
    root = tmp_path / ".omd"
    write_sentinel(root, "", time.time() - 7 * 3600)
    proc = run_hook({"cwd": str(tmp_path)})
    assert proc.returncode == 0
    assert "(slug unknown)" in proc.stdout
    assert (root / ".verify-pending").is_file()


def test_expire_stale_slugless_corrupt_json_treated_as_expired(tmp_path):
    """12) a slugless sentinel with unparseable JSON falls back to
    armed_at=0.0 (lines 38-39) -- always older than the TTL, so it is treated
    as expired and removed with a one-time Korean notice instead of raising
    or silently sticking around to nag forever (2026-07-15 vault incident
    failure class: corrupt sentinel data)."""
    root = tmp_path / ".omd"
    root.mkdir()
    sentinel = root / ".verify-pending"
    sentinel.write_text("{not valid json")
    notice = expire_stale_slugless(str(root))
    assert notice is not None
    assert "만료" in notice
    assert not sentinel.exists()


def test_slugged_sentinel_never_self_expires(tmp_path):
    """11) slugged sentinels mark real carried-over work (HK-4) — no TTL,
    however old."""
    root = tmp_path / ".omd"
    write_sentinel(root, "mydeck", time.time() - 30 * 24 * 3600)
    proc = run_hook({"cwd": str(tmp_path)})
    assert proc.returncode == 0
    assert "mydeck" in proc.stdout
    assert (root / "mydeck" / ".verify-pending").is_file()


# ── D2 (v0.6.2): 이월 센티널 세션당 1회 알림 (2026-07-21 매 턴 재경고 사고) ──
# stop_hook_active 는 한 Stop 안의 재진입 래치일 뿐 턴 간 억제가 아니라서,
# TTL 없는 이월(6h+) 센티널이 세션 내내(8회+) 매 Stop 재경고했다. 수정: 같은
# 이월 집합은 session_id 당 1회만 알린다. HK-4("real carried-over work stays
# visible")는 유지·정제 — 센티널은 여전히 만료되지 않고, 새 세션마다 첫 Stop
# 에서 반드시 1회 노출된다. 억제되는 것은 같은 세션 안의 반복뿐(§7 ⑥ alert
# fatigue — stage_evidence_gaps 의 named exception 과 같은 근거). 신선한(6h
# 이내) 센티널은 무변: 매 Stop 경고. 저장소는 HG-3 과 같은
# .omd/.hook-throttle.json, 킬스위치도 동일(OMD_REMINDER_COOLDOWN_SECONDS<=0).


def test_carried_over_notifies_once_per_session_but_every_new_session(tmp_path):
    """d2-1) 이월 센티널: 같은 session_id 두 번째 Stop 은 침묵, 센티널은 잔존,
    새 session_id 는 다시 1회 알림 (HK-4 가시성 유지의 핵심 증거)."""
    root = tmp_path / ".omd"
    write_sentinel(root, "olddeck", time.time() - 7 * 3600)
    p1 = run_hook({"cwd": str(tmp_path), "session_id": "sess-1"})
    assert "carried over" in p1.stdout
    p2 = run_hook({"cwd": str(tmp_path), "session_id": "sess-1"})
    assert p2.returncode == 0
    assert p2.stdout.strip() == ""
    assert (root / "olddeck" / ".verify-pending").is_file()  # TTL 아님
    p3 = run_hook({"cwd": str(tmp_path), "session_id": "sess-2"})
    assert "carried over" in p3.stdout


def test_fresh_sentinel_warns_every_stop_same_session(tmp_path):
    """d2-2) 신선한 센티널(이번 세션 무장)은 같은 세션에서도 매 Stop 경고 —
    억제는 이월분에만 적용된다."""
    root = tmp_path / ".omd"
    write_sentinel(root, "mydeck", time.time())
    for _ in range(2):
        proc = run_hook({"cwd": str(tmp_path), "session_id": "sess-1"})
        assert "mydeck" in proc.stdout


def test_mixed_second_stop_lists_only_fresh(tmp_path):
    """d2-3) 이월+신선 혼재: 첫 Stop 은 둘 다, 두 번째 Stop 은 신선분만."""
    root = tmp_path / ".omd"
    write_sentinel(root, "olddeck", time.time() - 7 * 3600)
    write_sentinel(root, "newdeck", time.time())
    p1 = run_hook({"cwd": str(tmp_path), "session_id": "s"})
    assert "olddeck" in p1.stdout and "newdeck" in p1.stdout
    p2 = run_hook({"cwd": str(tmp_path), "session_id": "s"})
    assert "newdeck" in p2.stdout
    assert "olddeck" not in p2.stdout


def test_no_session_id_never_suppresses(tmp_path):
    """d2-4) session_id 없는 payload(구버전 하네스·직접 실행)는 억제하지 않는다
    — 가시성 쪽으로 fail-open. 기존 테스트 전부가 이 경로라 동작 무변."""
    root = tmp_path / ".omd"
    write_sentinel(root, "olddeck", time.time() - 7 * 3600)
    for _ in range(2):
        proc = run_hook({"cwd": str(tmp_path)})
        assert "carried over" in proc.stdout


def test_suppression_kill_switch_env(tmp_path):
    """d2-5) OMD_REMINDER_COOLDOWN_SECONDS<=0 은 HG-3 와 동일하게 이월 억제도
    끈다 (같은 노이즈-억제 킬스위치 재사용)."""
    root = tmp_path / ".omd"
    write_sentinel(root, "olddeck", time.time() - 7 * 3600)
    env = {"OMD_REMINDER_COOLDOWN_SECONDS": "0"}
    p1 = run_hook({"cwd": str(tmp_path), "session_id": "sess-1"}, env=env)
    p2 = run_hook({"cwd": str(tmp_path), "session_id": "sess-1"}, env=env)
    assert "carried over" in p1.stdout
    assert "carried over" in p2.stdout
