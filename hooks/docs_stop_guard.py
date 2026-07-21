"""OMD Stop hook: advisory verify-pending reminder (G1). stdlib only, fail-open.

omd's #1 failure mode is "done" declared without a fresh render/verify. The
docs_verify_emit hook ARMS a `.omd/**/.verify-pending` sentinel on every document
build and CLEARS it when a verify-signal command runs; this hook, at Stop, lists
any sentinels still pending. Strictly advisory (D6): never `decision: block` —
deferring verify is legitimate, so the wording absorbs it (HK-2). Re-entry safe:
exits immediately when stop_hook_active (G1-chk). Carried-over sentinels are
announced once per session, not at every Stop (D2, v0.6.2 — see
suppress_notified_carryovers).
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from omd_atomic import atomic_write_json  # noqa: E402

SENTINEL = ".verify-pending"
STALE_AFTER = 6 * 3600  # older = carried over from an earlier session (HK-4)
# G7: slugged sentinels have no TTL (HK-4 — real carried-over work stays visible),
# but a SLUGLESS root sentinel names no .omd/<slug>/ workspace, so in a workspace
# that never runs verify signals nothing ever clears it — it would re-warn
# "(slug unknown)" at every Stop forever (2026-07-15 vault incident: a
# misclassified robotics command armed one in a repo with no document history).
SLUGLESS_EXPIRE_AFTER = 7 * 24 * 3600
EVIDENCE_LOG = "stage-evidence.log"
PILOT_STAGES = ("1", "2", "3", "4", "5", "6")  # intake..verify (docs-pilot Steps 1-6)
# D2 (v0.6.2): shared with docs_verify_emit's HG-3 reminder cooldown — same file,
# same atomic writer, same kill switch (OMD_REMINDER_COOLDOWN_SECONDS<=0).
THROTTLE_FILE = ".hook-throttle.json"
SEEN_TTL = 7 * 24 * 3600  # prune old entries so per-session keys never accumulate


def _armed_at(path):
    try:
        return float(json.load(open(path)).get("armed_at", 0) or 0)
    except Exception:
        return 0.0


def expire_stale_slugless(root: str):
    """G7: remove a slugless root sentinel past SLUGLESS_EXPIRE_AFTER and return
    a one-time final notice (None otherwise). An unparseable armed_at counts as
    expired — a corrupt slugless sentinel is pure noise. Fail-open: if removal
    fails, stay silent and retry at the next Stop."""
    path = os.path.join(root, SENTINEL)
    if not os.path.isfile(path):
        return None
    if time.time() - _armed_at(path) <= SLUGLESS_EXPIRE_AFTER:
        return None
    try:
        os.remove(path)
    except OSError:
        return None
    days = int(SLUGLESS_EXPIRE_AFTER // 86400)
    return (
        f"[OMD verify-pending] slug 없는 verify-pending 센티널이 {days}일 넘게 남아 있어 "
        "자동 만료·제거했습니다 (마지막 고지 — 대응 문서 워크스페이스 없음)."
    )


def pending_sentinels(root: str):
    found = []
    top = os.path.join(root, SENTINEL)
    if os.path.isfile(top):
        found.append(("(slug unknown)", top))
    if os.path.isdir(root):
        for d in sorted(os.listdir(root)):
            p = os.path.join(root, d, SENTINEL)
            if os.path.isfile(p):
                found.append((d, p))
    return found


def build_message(items):
    lines = []
    now = time.time()
    for slug, path in items:
        tag = (" — carried over from an earlier session"
               if now - _armed_at(path) > STALE_AFTER else "")
        lines.append(f"  - {slug}{tag}")
    return (
        "[OMD verify-pending] 이 세션에서 빌드된 문서 중 fresh verify가 아직 확인되지 않은 항목:\n"
        + "\n".join(lines)
        + "\n검증하려면 docs-verify(무결성 게이트+전수 정독). "
        "advisory입니다 — verify를 나중에 해도 무방하며, 의도적 유예라면 무시하고 진행하세요."
    )


def suppress_notified_carryovers(root, items, session_id):
    """D2 (v0.6.2): carried-over sentinels (armed_at past STALE_AFTER) used to
    re-warn at EVERY Stop — stop_hook_active is an in-Stop re-entry latch, not
    per-turn suppression (8+ repeats in one session, 2026-07-21). Now a given
    carried-over set is announced once per session_id. HK-4 ("real carried-over
    work stays visible") is kept, refined: sentinels still never expire, and
    every NEW session surfaces them again at its first Stop — only same-session
    repetition is absorbed (spec §7 ⑥ alert fatigue, the same rationale as
    stage_evidence_gaps' named exception). Fresh sentinels (this session's own
    work, by the same 6h proxy the stale tag uses) keep warning at every Stop.
    Reuses the HG-3 throttle store; OMD_REMINDER_COOLDOWN_SECONDS<=0 is the
    same kill switch; no session_id in the payload → no suppression, and a
    failed record → warn again next Stop (both fail open toward visibility)."""
    if not session_id or not items:
        return items
    try:
        if float(os.environ.get("OMD_REMINDER_COOLDOWN_SECONDS", 1)) <= 0:
            return items
    except ValueError:
        pass
    now = time.time()
    fresh, stale = [], []
    for item in items:
        (stale if now - _armed_at(item[1]) > STALE_AFTER else fresh).append(item)
    if not stale:
        return items
    # Key on the stale SET, not the session alone: a slug crossing the 6h line
    # (or getting verified) mid-session changes the set and earns one re-notice.
    key = hashlib.sha256(("stop-carryover:%s:%s" % (
        session_id, ",".join(sorted(slug for slug, _ in stale)))).encode("utf-8")).hexdigest()
    throttle = os.path.join(root, THROTTLE_FILE)
    try:
        seen = json.load(open(throttle, encoding="utf-8"))
    except Exception:
        seen = {}
    if not isinstance(seen, dict):
        seen = {}
    if key in seen:
        return fresh
    try:
        seen[key] = now
        seen = {k: v for k, v in seen.items()
                if isinstance(v, (int, float)) and now - v < SEEN_TTL}
        atomic_write_json(throttle, seen)
    except Exception:
        pass  # recording failure must not hide the notice
    return items


def stage_evidence_gaps(root):
    """G5: recent pilot runs (log mtime within STALE_AFTER) missing stage markers.

    The mtime cutoff is a NAMED exception to HK-4 (never silence stale leftovers):
    .verify-pending marks UNRESOLVED work so carry-overs stay visible, but this log
    is a finished run's delegation audit trail with no clearing event — re-warning
    every Stop about long-gone runs would reintroduce alert fatigue (spec §7 ⑥)."""
    gaps = []
    if not os.path.isdir(root):
        return gaps
    now = time.time()
    for d in sorted(os.listdir(root)):
        log = os.path.join(root, d, EVIDENCE_LOG)
        try:
            if not os.path.isfile(log) or now - os.path.getmtime(log) > STALE_AFTER:
                continue
            body = open(log, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        seen = set(re.findall(r"OMD stage (\d)", body))
        missing = [n for n in PILOT_STAGES if n not in seen]
        if missing:
            gaps.append((d, missing))
    return gaps


def build_evidence_message(gaps):
    lines = [f"  - {slug}: stage {', '.join(missing)}" for slug, missing in gaps]
    return (
        "[OMD stage-evidence] 최근 pilot 실행에서 spawned/skipped 마커가 없는 스테이지:\n"
        + "\n".join(lines)
        + "\n마커가 없다는 것은 해당 스테이지가 위임 없이 인라인 처리됐을 수 있다는 뜻입니다"
        " (author≠reviewer 분리 약화). advisory입니다 — 의도적 인라인이었다면 무시하세요."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if payload.get("stop_hook_active"):
            return 0  # G1-chk: never re-fire inside a stop-hook continuation
        root = os.path.join(payload.get("cwd") or os.getcwd(), ".omd")
        expiry_notice = expire_stale_slugless(root)  # G7: before listing pendings
        items = suppress_notified_carryovers(
            root, pending_sentinels(root), payload.get("session_id"))
        gaps = stage_evidence_gaps(root)
        blocks = []
        if expiry_notice:
            blocks.append(expiry_notice)
        if items:
            blocks.append(build_message(items))
        if gaps:
            blocks.append(build_evidence_message(gaps))
        if blocks:
            message = "\n\n".join(blocks)
            print(json.dumps({
                "systemMessage": message,
                "hookSpecificOutput": {
                    "hookEventName": "Stop",
                    "additionalContext": message,
                },
            }))
    except Exception:
        pass  # fail-open — a broken guard must never block Stop
    return 0


if __name__ == "__main__":
    sys.exit(main())
