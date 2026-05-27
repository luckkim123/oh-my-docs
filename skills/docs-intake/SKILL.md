---
name: docs-intake
description: |
  문서 작업 의중 파악 — 모호한 요청을 "무엇을 / 누구에게 / 왜 / 어떤 톤" 으로 Socratic 크리스탈화.
  발표자료·보고서·공문서 등 무엇을 만들지 아직 흐릿할 때 먼저 의도를 좁힌다. OMD 하네스의 1단계.
  Triggers: 발표자료 만들건데, 문서 만들어야 하는데 정리가 안 됐어, 뭘 만들지 모르겠어,
  intake, 의중 파악, 문서 기획, document intake, clarify document, 어떤 자료
---

# docs-intake — 의중 파악 (1단계)

<Purpose>
모호한 문서 요청을 실행 가능한 명세로 좁힌다. 무엇을(포맷·종류), 누구에게(청중), 왜(목적), 어떤 톤(디펜스/학회/강의)을 Socratic 질문으로 크리스탈화. OMC deep-interview 의 문서판.
</Purpose>

<Use_When>
- 사용자가 무엇을 만들지/어떤 톤일지 아직 흐릿하게 말할 때
- docs-pilot 의 첫 단계로 진입할 때
- "정리가 안 됐어", "뭘 만들지 모르겠어" 류
</Use_When>

<Do_Not_Use_When>
- 명세가 이미 또렷할 때 (포맷·청중·톤 다 정해짐) → 곧장 docs-plan 으로 skip
- 기존 문서를 *수정*만 하면 될 때 → docs-build (revision) 직행
</Do_Not_Use_When>

<Gate>
**게이트 0 — 의도 확정.** 아래가 모두 답해지면 통과; 하나라도 비면 질문:
무엇(포맷+문서종류) · 누구(청중) · 왜(목적) · 톤(프리셋) · 입력(소스 자료 위치).
</Gate>

<Steps>
1. 요청을 읽고 위 5개 중 비어 있는 것을 식별.
2. 비면 **한 번에 하나씩** 질문 (AskUserQuestion 다지선다 우선). 추측으로 채우지 말 것.
3. 모두 답해지면 doc-analyzer 를 dispatch 해 입력·기존 양식을 파악:
   `Task(subagent_type="oh-my-docs:doc-analyzer", ...)`
4. 의도 명세 + analyzer 인벤토리를 게이트 0 으로 사용자에게 제시 → 확인.
</Steps>

<Output>
의도 명세: {포맷, 문서종류, 청중, 목적, 톤 프리셋, 입력 경로} + analyzer 의 소스 인벤토리.
다음 단계(docs-plan)가 그대로 받을 수 있는 형태.
</Output>
