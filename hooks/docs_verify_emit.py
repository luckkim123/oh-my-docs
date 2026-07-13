"""OMD PostToolUse hook: when a Bash command builds/converts a document artifact
(.pptx/.docx/.xlsx/.hwpx via python-pptx / python-docx / openpyxl / soffice), inject a
document-integrity reminder (stdlib only, fail-open).

Why Bash (not Edit|Write): OMD does not edit .pptx/.docx in place — those are
binary. doc-builder WRITES a python build script and RUNS it with Bash to
produce the artifact (or runs `soffice --convert-to`). So the document is born
from a Bash command, and that is what this hook watches. (oms watches Edit|Write
because .tex/.bib are text edited directly — different domain, different trigger.)

This is the freeze-safe variant of OMC's post-tool-verifier. OMC injects "fix
before continuing" on write — a phrasing observed to freeze the model (reads as
an imperative gate). This hook only REMINDS to verify via docs-inspect/
docs-verify; it never says "fix before continuing" and never instructs a silent
auto-fix.

Noise control: most Bash commands are not document builds, so the hook stays
SILENT unless a build/convert signal AND a document extension both appear. A
read-only render (pdftoppm) or integrity check (unzip -t) alone does not trigger
it. Fail-open: any error returns 0 so the session is never blocked."""
import json
import re
import sys

# Build/convert signals — generation, not read-only inspection. These name the
# engine/convert explicitly, so they fire on their own (an extension confirms intent).
BUILD_SIGNALS = (
    "python-pptx", "python-docx", "from pptx", "import pptx",
    "from docx", "import docx", "Presentation(", "Document(",
    "openpyxl", "xlsxwriter", "Workbook(",
    "soffice --convert", "libreoffice --convert", "--convert-to",
)
# Builder's recommended path is "Write a build script, then run `python3 build.py`"
# (doc-builder Tool_Usage). Such a command may name NEITHER an engine string NOR a
# .pptx inline — so the signal+ext pair above misses it, and the hook stays silent
# on the exact path the harness tells the builder to use. Catch a python script
# run whose name hints at document building (build/deck/slide/doc/pptx/docx/hwpx),
# so an unrelated `python3 analyze_runs.py` does NOT trigger (noise control).
RUN_SCRIPT_RE = re.compile(
    r"\bpython3?\b[^\n|&;]*\b\w*(build|deck|slide|doc|pptx|docx|xlsx|hwpx|present)\w*\.py\b",
    re.IGNORECASE,
)


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
    has_signal = any(sig in command for sig in BUILD_SIGNALS)
    runs_doc_script = bool(RUN_SCRIPT_RE.search(command))
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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open: 입력 파싱 실패해도 세션 막지 않음

    if payload.get("tool_name", "") != "Bash":
        return 0
    command = (payload.get("tool_input", {}) or {}).get("command", "")

    # 문서 산출/변환 명령일 때만 리마인더. 그 외 Bash 는 침묵.
    if not is_doc_build(command):
        return 0

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": build_reminder(),
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
