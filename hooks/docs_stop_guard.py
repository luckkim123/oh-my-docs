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
import sys
import time

SENTINEL = ".verify-pending"
STALE_AFTER = 6 * 3600  # older = carried over from an earlier session (HK-4; no TTL expiry)


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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if payload.get("stop_hook_active"):
            return 0  # G1-chk: never re-fire inside a stop-hook continuation
        root = os.path.join(payload.get("cwd") or os.getcwd(), ".omd")
        items = pending_sentinels(root)
        if items:
            print(json.dumps({
                "systemMessage": build_message(items),
                "hookSpecificOutput": {
                    "hookEventName": "Stop",
                    "additionalContext": build_message(items),
                },
            }))
    except Exception:
        pass  # fail-open — a broken guard must never block Stop
    return 0


if __name__ == "__main__":
    sys.exit(main())
