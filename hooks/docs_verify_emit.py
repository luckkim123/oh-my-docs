"""OMD PostToolUse hook: when a Bash command builds/converts a document artifact
(.pptx/.docx/.hwpx via python-pptx / python-docx / soffice), inject a
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
import sys

DOC_EXTS = (".pptx", ".docx", ".hwpx")
# Build/convert signals — generation, not read-only inspection.
BUILD_SIGNALS = (
    "python-pptx", "python-docx", "from pptx", "import pptx",
    "from docx", "import docx", "Presentation(", "Document(",
    "soffice --convert", "libreoffice --convert", "--convert-to",
)


def is_doc_build(command: str) -> bool:
    """True only when the command both signals a build/convert AND names a
    document extension — so read-only renders/checks stay silent."""
    if not command:
        return False
    has_signal = any(sig in command for sig in BUILD_SIGNALS)
    names_doc = any(ext in command for ext in DOC_EXTS)
    return has_signal and names_doc


def build_reminder() -> str:
    return (
        "[OMD document-integrity reminder] 문서 산출/변환 명령이 실행됨.\n"
        "- 산출 후 docs-verify 로 무결성 5/5(zip CRC·엔진 파싱·soffice·dangling rels·orphan master) "
        "+ 전수 정독을 확인할 것. 형성적 개선점은 docs-inspect.\n"
        "- ⚠️ '열리는 것 같다'는 검증이 아니다 — fresh 렌더 증거 없이 done 선언 금지. "
        "원본 in-place 수정 금지(outputs/<doc>/current + versions/ 스냅샷).\n"
        "- pptx/docx/hwpx 포맷 원형 유지(임의 변환 금지). 수식은 카드가 VERIFIED 표시한 경로만."
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
