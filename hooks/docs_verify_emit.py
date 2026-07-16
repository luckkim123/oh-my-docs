"""OMD PostToolUse hook: when a Bash command builds/converts a document artifact
(.pptx/.docx/.xlsx/.hwpx via python-pptx / python-docx / openpyxl / soffice), inject a
document-integrity reminder (stdlib only, fail-open).
R2 (D5): md-genre deliverables are text born via Edit|Write — a second trigger
watches those, scoped to outputs/ paths with slug context.

Why Bash (not Edit|Write): OMD does not edit .pptx/.docx in place — those are
binary. doc-builder WRITES a python build script and RUNS it with Bash to
produce the artifact (or runs `soffice --convert-to`). So the document is born
from a Bash command, and that is what this hook watches. (oms watches Edit|Write
because .tex/.bib are text edited directly — different domain, different trigger.)
(Office formats only — see the D5 note above for md genres.)

This is the freeze-safe variant of OMC's post-tool-verifier. OMC injects "fix
before continuing" on write — a phrasing observed to freeze the model (reads as
an imperative gate). This hook only REMINDS to verify via docs-inspect/
docs-verify; it never says "fix before continuing" and never instructs a silent
auto-fix.

Noise control: most Bash commands are not document builds, so the hook stays
SILENT unless a build/convert signal AND a document extension both appear. A
read-only render (pdftoppm) or integrity check (unzip -t) alone does not trigger
it. Fail-open: any error returns 0 so the session is never blocked."""
import hashlib
import json
import os
import re
import sys
import tempfile
import time

# Build/convert signals — generation, not read-only inspection. These name the
# engine/convert explicitly, so they fire on their own (an extension confirms intent).
BUILD_SIGNALS = (
    "python-pptx", "python-docx", "from pptx", "import pptx",
    "from docx", "import docx", "Presentation(", "Document(",
    "openpyxl", "xlsxwriter", "Workbook(",
    "soffice --convert", "libreoffice --convert", "--convert-to",
    "mkdocs build",   # site genre — plain build arms; a --strict run is a verify (below)
)
# Builder's recommended path is "Write a build script, then run `python3 build.py`"
# (doc-builder Tool_Usage). Such a command may name NEITHER an engine string NOR a
# .pptx inline — so the signal+ext pair above misses it, and the hook stays silent
# on the exact path the harness tells the builder to use. Catch a python script
# run whose name hints at document building (build/deck/slide/doc/pptx/docx/xlsx/hwpx/present),
# so an unrelated `python3 analyze_runs.py` does NOT trigger (noise control).
RUN_SCRIPT_RE = re.compile(
    r"\bpython3?\b[^\n|&;]*\b(\w*(?:build|deck|slide|doc|pptx|docx|xlsx|hwpx|present)\w*\.py)\b",
    re.IGNORECASE,
)
# v0.5.1: test runs are never deliverable builds. `pytest tests/test_wiki_spec_docs.py`
# matched the doc-keyword heuristic above ("doc" in the TEST file name), armed a
# .verify-pending in a foreign repo, and the Stop guard re-warned every turn
# (2026-07-16 false-positive). Word-level pytest/unittest kills the whole check;
# a directly-run test_*.py / *_test.py script is filtered on the captured name.
TEST_RUN_RE = re.compile(r"\b(?:pytest|unittest)\b")

# G1: verify-pending sentinel handshake — armed on build, cleared on a
# verify-signal command, enforced (advisory) by hooks/docs_stop_guard.py at Stop.
VERIFY_SIGNALS = ("pdftoppm", "unzip -t", "markdownlint")


def is_verify_run(command: str) -> bool:
    """Verify-stage runs clear the sentinel and are matched BEFORE build signals:
    `mkdocs build --strict` is the site card's gate ① (a verify), while a plain
    `mkdocs build` is a build. Flag order varies, so match the token pair."""
    if any(sig in command for sig in VERIFY_SIGNALS):
        return True
    return "mkdocs" in command and "--strict" in command


SLUG_RE = re.compile(r"(?:\.omd|outputs)/([^/\s'\"]+)/")
SENTINEL = ".verify-pending"

# D5 (R2): md-genre artifacts (repo-docs, site) are text — born via Edit|Write,
# not Bash. Trigger is narrowed to deliverable paths (outputs/<slug>/**/*.md)
# WITH slug context (.omd/<slug>/ exists) so ordinary md editing stays silent
# (spec §7 risk ②). Work-area md (.omd/<slug>/build-notes.md, consensus/*.md)
# is not a deliverable and never arms (§7 ⑥ alert fatigue).
MD_EXTS = (".md", ".markdown")


def slug_from_md_path(file_path):
    """First path segment after an `outputs/` component (HK-3). Textual, so it
    handles absolute and relative paths, single-file (outputs/<slug>/current.md),
    artifact-set members and nested site trees identically."""
    parts = [p for p in os.path.normpath(file_path).split(os.sep) if p]
    for i, part in enumerate(parts[:-1]):
        if part == "outputs":
            return parts[i + 1]
    return None

# HG-3: same-content reminder cooldown — silences repeat message noise only;
# sentinel arm (G1 state) always happens regardless of throttling.
THROTTLE_FILE = ".hook-throttle.json"
DEFAULT_COOLDOWN = 600.0


def _omd_root(payload):
    return os.path.join(payload.get("cwd") or os.getcwd(), ".omd")


def _sentinel_path(root, command):
    m = SLUG_RE.search(command)
    return os.path.join(root, m.group(1), SENTINEL) if m else os.path.join(root, SENTINEL)


def _write_sentinel(path, head):
    """Atomic write (ST-1): half-written sentinels must never exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = json.dumps({"armed_at": time.time(), "command_head": head[:80]})
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-verify-")
    with os.fdopen(fd, "w") as f:
        f.write(body)
    os.replace(tmp, path)


def arm_sentinel(root, command):
    # v0.5.1 noise control: only an existing .omd/ project can be armed — never
    # fabricate .omd/ in a repo the pipeline has not touched. Mirrors
    # handle_md_edit's "no slug context -> not an omd artifact" rule.
    if not os.path.isdir(root):
        return
    _write_sentinel(_sentinel_path(root, command), command)


def clear_sentinels(root, command):
    # ponytail: clearing heuristic is command-string sniffing; upgrade to explicit
    # verify-stage signaling if false-clears surface
    if not os.path.isdir(root):
        return  # defensive: callable safely outside main()'s try envelope
    m = SLUG_RE.search(command)
    targets = ([os.path.join(root, m.group(1), SENTINEL)] if m
               else [os.path.join(root, SENTINEL)]
               + [os.path.join(root, d, SENTINEL) for d in os.listdir(root)
                  if os.path.isdir(os.path.join(root, d))])
    for t in targets:
        try:
            os.remove(t)
        except OSError:
            pass


def is_doc_build(command: str) -> bool:
    """True when the command signals a build/convert. Two routes:
    (a) an explicit engine/convert signal (`from pptx`, `--convert-to`, …) — fires
        on its own, since these name the engine/convert unambiguously; or
    (b) running a doc-named python script (`python3 build_deck.py`) — the builder's
        own recipe, which often names neither the engine nor a .pptx inline.
    Read-only renders/checks (pdftoppm, unzip -t) and unrelated scripts
    (`python3 analyze_runs.py`) match neither and stay silent (noise control)."""
    if not command:
        return False
    if TEST_RUN_RE.search(command):
        return False  # test runs never build a deliverable (v0.5.1)
    has_signal = any(sig in command for sig in BUILD_SIGNALS)
    m = RUN_SCRIPT_RE.search(command)
    name = m.group(1).lower() if m else ""
    runs_doc_script = bool(m) and not (name.startswith("test_") or name.endswith("_test.py"))
    return has_signal or runs_doc_script


def build_reminder() -> str:
    return (
        "[OMD document-integrity reminder] 문서 산출/변환 명령이 실행됨.\n"
        "- 산출 직후 **shape 어서션**(body run 에 font.size 명시·모든 shape width/height>0·"
        "폰트가 템플릿과 일치(테마 Calibri 추락 아님)·placeholder 잔존 프롬프트 0)을 코드로 확인할 것 — "
        "PNG 육안으로는 폰트 추락·width=0 증발이 안 잡힌다(2026-06-16 v4/v5). 어서션 통과 후에만 done.\n"
        "- 그 다음 docs-verify 로 무결성 5/5(zip CRC·엔진 파싱·soffice·dangling rels·orphan master) "
        "+ 전수 정독을 확인할 것. 형성적 개선점은 docs-inspect.\n"
        "- ⚠️ '열리는 것 같다'는 검증이 아니다 — fresh 렌더 증거 없이 done 선언 금지. "
        "원본 in-place 수정 금지(최종본은 outputs/<slug>/current 하나, 버전 스냅샷은 .omd/<slug>/versions/).\n"
        "- pptx/docx/xlsx/hwpx 포맷 원형 유지(임의 변환 금지). 수식은 카드가 VERIFIED 표시한 경로만."
    )


def site_build_reminder() -> str:
    return (
        "[OMD document-integrity reminder] site 빌드 명령이 실행됨 (mkdocs).\n"
        "- 산출 빌드 후 docs-verify 로 카드 gate 를 실행할 것 — references/formats/site.md: "
        "mkdocs build --strict [validation 블록 필수] / markdownlint / 내부 링크·앵커 / "
        "built HTML fresh-read / nav 완결성.\n"
        "- built HTML 은 .omd/<slug>/site-build/ — outputs/<slug>/current/ 안에 site/ 를 만들지 말 것 (D4).\n"
        "- ⚠️ fresh 실행 증거 없이 done 선언 금지 — '빌드가 돌았다'는 검증이 아니다."
    )


def md_reminder(slug: str) -> str:
    return (
        "[OMD document-integrity reminder] 텍스트 산출물(.md) 편집 감지 (slug: %s).\n"
        "- 편집을 마치면 docs-verify 로 카드가 정의한 **verify gate** 를 실행할 것 — "
        "repo-docs 는 references/formats/repo-docs.md 의 gate(필수 섹션·순서 / 내부 링크 / "
        "markdownlint / 코드블록 언어 태그 / ISO 날짜·버전 역순 / placeholder 스캔), "
        "site 는 references/formats/site.md 의 gate(mkdocs build --strict [validation 블록 필수] / "
        "markdownlint / 내부 링크·앵커 / built HTML fresh-read / nav 완결성).\n"
        "- ⚠️ fresh 실행 증거 없이 done 선언 금지 — '읽어보니 괜찮다'는 검증이 아니다.\n"
        "- 다중 파일 산출물의 계약은 outputs/<slug>/current/ + .omd/<slug>/manifest.json "
        "(references/output-layout.md)." % slug
    )


def handle_md_edit(payload) -> int:
    try:
        file_path = (payload.get("tool_input", {}) or {}).get("file_path", "") or ""
        if not file_path.lower().endswith(MD_EXTS):
            return 0
        slug = slug_from_md_path(file_path)
        if not slug:
            return 0
        root = _omd_root(payload)
        if not os.path.isdir(os.path.join(root, slug)):
            return 0  # no slug context → not an omd pipeline artifact (noise control)
        _write_sentinel(os.path.join(root, slug, SENTINEL), "edit:" + file_path)
        reminder = md_reminder(slug)
        if reminder_throttled(root, reminder):
            return 0
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": reminder,
        }}))
        return 0
    except Exception:
        return 0  # fail-open


def _cooldown_seconds():
    try:
        return float(os.environ.get("OMD_REMINDER_COOLDOWN_SECONDS", DEFAULT_COOLDOWN))
    except ValueError:
        return DEFAULT_COOLDOWN


def reminder_throttled(root: str, message: str) -> bool:
    """True → suppress this reminder (same content within cooldown). Fail-open: any
    IO/JSON error answers False (fire the reminder — silence is the risky side)."""
    cooldown = _cooldown_seconds()
    if cooldown <= 0:
        return False
    path = os.path.join(root, THROTTLE_FILE)
    digest = hashlib.sha256(message.encode("utf-8")).hexdigest()
    now = time.time()
    try:
        with open(path, encoding="utf-8") as f:
            seen = json.load(f)
    except Exception:
        seen = {}
    throttled = isinstance(seen, dict) and now - float(seen.get(digest, 0) or 0) < cooldown
    if not throttled:
        try:
            seen = seen if isinstance(seen, dict) else {}
            seen[digest] = now
            fd, tmp = tempfile.mkstemp(dir=root, prefix=".tmp-throttle-")
            with os.fdopen(fd, "w") as f:
                json.dump(seen, f)
            os.replace(tmp, path)
        except Exception:
            pass  # recording failure must not suppress the reminder
    return throttled


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open: 입력 파싱 실패해도 세션 막지 않음

    if not isinstance(payload, dict):
        return 0  # fail-open: valid JSON but not an object

    tool = payload.get("tool_name", "")
    if tool in ("Edit", "Write"):
        return handle_md_edit(payload)
    if tool != "Bash":
        return 0
    command = (payload.get("tool_input", {}) or {}).get("command", "")

    # verify 실행이 최우선 — strict 빌드가 BUILD_SIGNALS 에 걸려 재-arm 되는 것 방지 (결정 2).
    try:
        if command and is_verify_run(command):
            clear_sentinels(_omd_root(payload), command)
            return 0
    except Exception:
        pass  # fail-open

    # 문서 산출/변환 명령일 때만 리마인더. 그 외 Bash 는 침묵.
    if not is_doc_build(command):
        return 0

    try:
        arm_sentinel(_omd_root(payload), command)
    except Exception:
        pass  # fail-open: sentinel is best-effort, reminder still fires

    reminder = site_build_reminder() if "mkdocs" in command else build_reminder()
    try:
        if reminder_throttled(_omd_root(payload), reminder):
            return 0
    except Exception:
        pass  # fail-open: on any doubt, fire the reminder

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": reminder,
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
