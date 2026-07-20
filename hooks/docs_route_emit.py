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

Relevance gate (wave-17, ported from oms's is_paper_related): the gate only
decides WHETHER to inject, never WHAT — a true positive (project marker OR a
high-specificity docs keyword) prints the exact same CHECKPOINT literal below,
byte-for-byte, via the single _emit_checkpoint() assembly. Rollout is a
3-state OMD_ROUTE_GATE env flag (off/observe/on), default "off": the gate code
is fully bypassed and today's unconditional inject is unchanged.
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

CHECKPOINT = (
    "<omd-routing>\n"
    "문서 작업 요청(.pptx/.docx/.xlsx/.hwpx 생성·수정·검토·양식추출)이면, 행동 전에 한 줄로 판정하라:\n"
    "- 포맷: pptx / docx / xlsx / hwpx / repo-docs / site — references/formats/<format>.md 카드가 도구·함정·수식의 단일 진실.\n"
    "  (repo-docs = README·CHANGELOG 등 GitHub 저장소 문서 세트 / site = MkDocs+Material 문서 사이트 — "
    "둘 다 텍스트 장르, 산출은 artifact-set(outputs/<slug>/current/), 엔진은 마크다운+빌린 린터/빌더 체인.)\n"
    "  (pdf 는 생성 포맷이 아니라 입력·변환 층위 — 입력=docs-pdf, 변환 타깃=docs-convert. FORMAT 판정에 pdf 를 넣지 말 것.)\n"
    "- 단계: intake(의중) / standardize(양식추출) / plan(구조) / build(산출) / "
    "inspect(형성적 검토) / verify(총괄 검증) / revise(통과까지 루프), 또는 docs-pilot(통째).\n"
    "- 메타 단계: learn(관찰→style-spec 기본값 승격, 사람 게이트) — 운영 중 .omd/learned.md 에 쌓인 "
    "관찰을 강제 style 기본값으로 굳힐 때만. 자동 발동 아님(heavy=사람 게이트). content 는 승격 대상 아님(form 만).\n"
    "단일 단계면 그 스킬 직접, 브리프→완성이면 docs-pilot. 수식은 카드가 VERIFIED 표시한 경로만.\n"
    "⚠️ Deliberate(디펜스·심사·외부 공식 발표)면 plan은 `docs-plan --consensus`(RALPLAN-DR) — "
    "한 줄 근거에 `--consensus` 발동 여부를 밝혀라.\n"
    "⚠️ 지식 SSOT 우선(첫 생성·방향 제시 전 필독): 디자인 시스템·양식·문체·빌드 규칙·주석 기법 등 "
    "'이 산출물은 어떻게 만드나'를 묻거나 판단해야 하면, 소스·일반 관행·내 기억보다 먼저 이 프로젝트의 "
    ".omd/wiki/(convention·pattern·decision·reference) 를 SSOT 로 읽어라. wiki 에 답이 있는데 즉흥적으로 "
    "스타일을 정하는 것은 결함이다. 그리고 .omd/<slug>/ 존재를 확인하라 — 있으면 이 산출물은 "
    "진행 중(build·versions·renders·content.json)이니 기존 build 파이프라인·템플릿을 재사용하라. "
    "빈 Presentation()/백지에서 새로 짜는 것은 금지. 이 확인 전에는 '이렇게 개선하겠다'는 "
    "방향 제시도 하지 마라 — 지형 미파악 상태의 방향 제시가 백지 재시작으로 직결된다.\n\n"
    "문서 작업이면, 판정을 응답 맨 앞 omha ROUTE 줄 바로 다음에 이 한 줄로 출력하라(누락 금지):\n"
    "STAGE(docs) → <intake|standardize|plan|build|inspect|verify|revise|learn|docs-pilot> · <pptx|docx|xlsx|hwpx|repo-docs|site> · <한 줄 근거>\n"
    "문서 작업이 아니면 이 블록 전체 무시(STAGE 줄도 출력하지 말 것).\n"
    "</omd-routing>"
)

# --- relevance gate (wave-17) -------------------------------------------------
# High-specificity docs-domain tokens only. Deliberately excludes polysemous
# bare verbs (만들어/생성/빌드/make/build/generate) — they appear in nearly every
# coding turn, so including them would erase the injection-tax savings this
# gate exists for (spec §5). A project marker (.omd/) covers those turns anyway.
_CJK_TOKENS = (
    "발표자료", "슬라이드", "문서", "보고서", "양식", "아웃라인", "스토리라인", "목차", "템플릿",
)
_DOT_TOKENS = (".pptx", ".docx", ".xlsx", ".hwpx")
_ASCII_TOKENS = (
    "pptx", "docx", "xlsx", "hwpx", "slide", "slides", "presentation", "deck",
    "powerpoint", "document", "outline", "readme", "changelog", "mkdocs", "docs-pilot",
)
_ASCII_RE = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in _ASCII_TOKENS) + r")\b")


def _has_omd_marker() -> bool:
    return (Path.cwd() / ".omd").is_dir()


def is_docs_related(prompt) -> bool:
    """True when a project-state marker (.omd/) is present, prompt is
    missing/not-a-string (fail-toward-inject), or any docs-domain token
    matches. Never raises -- an internal error (including a marker-probe
    failure) also fails toward injection."""
    try:
        if _has_omd_marker():
            return True
        if not isinstance(prompt, str):
            return True
        lowered = prompt.lower()
        if any(tok in lowered for tok in _CJK_TOKENS):
            return True
        if any(tok in lowered for tok in _DOT_TOKENS):
            return True
        return bool(_ASCII_RE.search(lowered))
    except Exception:
        return True  # gate exception -> inject


def _gate_mode() -> str:
    try:
        v = os.environ.get("OMD_ROUTE_GATE", "off").strip().lower()
    except Exception:
        return "off"
    return v if v in ("off", "observe", "on") else "off"


def _log_would_suppress(prompt) -> None:
    """observe-mode audit trail (rollout §6): one stderr line per turn the gate
    would have suppressed, so real-traffic false-negative risk can be measured
    before flipping to "on". Best-effort — never raises, never touches stdout
    (byte-identity of the injected context is untouched)."""
    try:
        digest = (hashlib.sha256(prompt.encode("utf-8", "replace")).hexdigest()[:16]
                  if isinstance(prompt, str) else "none")
        sys.stderr.write(json.dumps({"decision": "would-suppress", "prompt_hash": digest}) + "\n")
    except Exception:
        pass


def _emit_checkpoint() -> None:
    out = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": CHECKPOINT,
        }
    }
    print(json.dumps(out))


def main() -> int:
    try:
        mode = _gate_mode()
        if mode == "off":
            _emit_checkpoint()  # today's unconditional inject, unchanged
            return 0
        try:
            payload = json.load(sys.stdin)
        except Exception:
            payload = None
        prompt = payload.get("prompt") if isinstance(payload, dict) else None
        relevant = is_docs_related(prompt)
        if mode == "observe":
            if not relevant:
                _log_would_suppress(prompt)
            _emit_checkpoint()  # observe never suppresses — logging only
            return 0
        if not relevant:
            return 0  # mode == "on": enforce
        _emit_checkpoint()
    except Exception:
        return 0  # fail-open — never block the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
