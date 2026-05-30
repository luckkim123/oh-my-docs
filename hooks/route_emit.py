"""oh-my-docs UserPromptSubmit hook: inject a document-routing checkpoint.

Stdlib only (no runtime deps — a test enforces this). The hook does NOT decide
anything itself; it injects a one-line checkpoint that reminds the session LLM,
when a document request is detected, to route format + stage before acting. The
actual format/trap knowledge lives in references/formats/*.md (single source of
truth) and the stage logic in skills/docs-*/SKILL.md — this hook never embeds
that knowledge inline, so there is no drift.

Layering: omha (the meta-harness) picks the LANE (superpowers / oh-my-claudecode
/ handle-directly). This OMD hook fires only inside the document domain — it
picks FORMAT + STAGE within that lane. The two do not conflict.

MVP: static checkpoint text (no keyword parsing). Stage 2 may add dynamic
format-keyword detection that reads the skills' Triggers. Fail-open: any error
returns 0 so the session is never blocked.
"""
import json
import sys

CHECKPOINT = (
    "<omd-routing>\n"
    "문서 작업 요청(.pptx/.docx/.xlsx/.hwpx 생성·수정·검토·양식추출)이면, 행동 전에 한 줄로 판정하라:\n"
    "- 포맷: pptx / docx / xlsx / hwpx — references/formats/<format>.md 카드가 도구·함정·수식의 단일 진실.\n"
    "- 단계: intake(의중) / standardize(양식추출) / plan(구조) / build(산출) / "
    "inspect(형성적 검토) / verify(총괄 검증) / revise(통과까지 루프), 또는 docs-pilot(통째).\n"
    "- 메타 단계: learn(관찰→style-spec 기본값 승격, 사람 게이트) — 운영 중 .omd/learned.md 에 쌓인 "
    "관찰을 강제 style 기본값으로 굳힐 때만. 자동 발동 아님(heavy=사람 게이트). content 는 승격 대상 아님(form 만).\n"
    "단일 단계면 그 스킬 직접, 브리프→완성이면 docs-pilot. 수식은 카드가 VERIFIED 표시한 경로만.\n"
    "⚠️ Deliberate(디펜스·심사·외부 공식 발표)면 plan은 `docs-plan --consensus`(RALPLAN-DR) — "
    "한 줄 근거에 `--consensus` 발동 여부를 밝혀라.\n\n"
    "문서 작업이면, 판정을 응답 맨 앞 omha ROUTE 줄 바로 다음에 이 한 줄로 출력하라(누락 금지):\n"
    "STAGE(docs) → <intake|standardize|plan|build|inspect|verify|revise|learn|docs-pilot> · <pptx|docx|xlsx|hwpx> · <한 줄 근거>\n"
    "문서 작업이 아니면 이 블록 전체 무시(STAGE 줄도 출력하지 말 것).\n"
    "</omd-routing>"
)


def main() -> int:
    try:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": CHECKPOINT,
            }
        }
        print(json.dumps(out))
    except Exception:
        return 0  # fail-open — never block the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
