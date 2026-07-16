"""OMD Stop hook: advisory verify-pending reminder (G1). stdlib only, fail-open.

omd's #1 failure mode is "done" declared without a fresh render/verify. The
docs_verify_emit hook ARMS a `.omd/**/.verify-pending` sentinel on every document
build and CLEARS it when a verify-signal command runs; this hook, at Stop, lists
any sentinels still pending. Strictly advisory (D6): never `decision: block` —
deferring verify is legitimate, so the wording absorbs it (HK-2). Re-entry safe:
exits immediately when stop_hook_active (G1-chk).
"""
import json
import os
import re
import sys
import time

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


def expire_stale_slugless(root: str):
    """G7: remove a slugless root sentinel past SLUGLESS_EXPIRE_AFTER and return
    a one-time final notice (None otherwise). An unparseable armed_at counts as
    expired — a corrupt slugless sentinel is pure noise. Fail-open: if removal
    fails, stay silent and retry at the next Stop."""
    path = os.path.join(root, SENTINEL)
    if not os.path.isfile(path):
        return None
    try:
        armed = float(json.load(open(path)).get("armed_at", 0) or 0)
    except Exception:
        armed = 0.0
    if time.time() - armed <= SLUGLESS_EXPIRE_AFTER:
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
        try:
            armed = json.load(open(path)).get("armed_at", 0)
        except Exception:
            armed = 0
        tag = " — carried over from an earlier session" if now - armed > STALE_AFTER else ""
        lines.append(f"  - {slug}{tag}")
    return (
        "[OMD verify-pending] 이 세션에서 빌드된 문서 중 fresh verify가 아직 확인되지 않은 항목:\n"
        + "\n".join(lines)
        + "\n검증하려면 docs-verify(무결성 게이트+전수 정독). "
        "advisory입니다 — verify를 나중에 해도 무방하며, 의도적 유예라면 무시하고 진행하세요."
    )


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
        items = pending_sentinels(root)
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
