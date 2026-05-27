---
name: docs-inspect
description: |
  작업중인 발표자료/문서를 형성적으로 검토 — PPTEval 3축(Content/Design/Coherence)으로 개선점을
  순위 매겨 제시. 아직 고칠 수 있는 단계의 조언이지 합격/불합격 판정이 아니다(그건 docs-verify).
  Triggers: 이거 어때, 검토해줘, 발표자료 봐줘, 피드백, 개선점, 지금 상태 어때,
  review document, critique, inspect, 슬라이드 검토, 보완할 점
---

# docs-inspect — 작업중 검토 (형성적)

<Purpose>
작업 중인 문서를 형성적으로 비평한다. PPTEval 3축으로 개선점을 *순위 매겨* 제시 — 아직 변경이 싼 단계의 조언. ppt-edit 가 검증만 했던 것을 능동적 비평으로 분리·고도화.
</Purpose>

<Use_When>
- 사용자가 "지금 이거 어때?" 하고 작업중 문서를 던질 때
- docs-pilot 산출 후 verify 전, 개선 루프를 돌 때
- 독립 진입: pilot 안 거치고 바로 검토만 원할 때
</Use_When>

<Do_Not_Use_When>
- 최종 합격/불합격 게이트가 필요할 때 → docs-verify (총괄)
- 산출물이 아직 없을 때 → docs-build 먼저
</Do_Not_Use_When>

<Rubric>
references/rubrics/ppteval.md 가 3축 정의의 단일 진실: Content(메시지·근거·placeholder·density) /
Design(폰트·컬러·overflow·clipping, ≥150dpi 렌더) / Coherence(arc·전환·일관성).
</Rubric>

<Steps>
**기본 (작은 deck)** — 단일 inspector:
1. doc-inspector 를 dispatch:
   `Task(subagent_type="oh-my-docs:doc-inspector", ...)`
2. inspector 가 ≥150dpi 전수 렌더 → 읽고 → 3축 개선점을 impact 순위로.

**다관점 (큰 deck / 정밀 검토)** — 3 렌즈 병렬 (ralplan critic 패턴):
1. doc-inspector 를 **3개 병렬** dispatch, 각자 한 축에만 집중:
   - 렌즈 1: Content (메시지·근거·placeholder·density)
   - 렌즈 2: Design (폰트·컬러·overflow·clipping, ≥150dpi)
   - 렌즈 3: Coherence (arc·전환·일관성)
   `Task(subagent_type="oh-my-docs:doc-inspector", ...)` × 3 (프롬프트로 축 지정)
2. 3 렌즈 결과를 병합, 축별 충돌 없이 impact 순위로 통합.

**공통**:
3. 순위 개선 리스트를 사용자에게 제시 (조언 — 판정 아님).
</Steps>

<Multi_Lens_When>
다관점은 큰 deck(20+ 슬라이드)이나 정밀 검토가 필요할 때. 작은 deck 은 단일 inspector 가 3축을 한 번에 — 3렌즈는 overkill. 어느 쪽이든 inspector 는 builder 와 다른 lane(self-approval 금지).
</Multi_Lens_When>

<Output>
순위 매긴 개선 리스트 (각 항목: 축 / 위치 / 발견 / 권장 수정). 합격 판정은 하지 않음 — verify 로.
</Output>

<Separation>
inspect 는 절대 "done/approved" 라 하지 않는다. 형성(개선점)과 총괄(합격선)은 다른 lane,
그리고 어느 쪽도 산출한 builder 와 같은 컨텍스트가 자기 승인하지 않는다.
</Separation>
