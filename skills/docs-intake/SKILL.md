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
4. **Round 0 — Topology** (게이트 0 통과 후, scholar-deepen과 동형): 문서의 top-level component를 잠근다 (흔히 3-6개) — 섹션 + 메시지 클러스터(전달할 핵심 메시지 묶음) + 자료 단위(figure/table/근거). depth-first로 한 갈래만 파다 sibling을 가리는 것을 막는다.
5. **차원별 명확/모호 정성 판정** (4차원, 수치 없음 — 정성):
   - **Audience clarity**: 청중이 또렷한가? (누가, 무엇을 이미 아는가, 무엇을 기대하나)
   - **Message clarity**: 이 발표의 한 문장 핵심 메시지가 또렷한가? 여러 메시지가 섞여 흐린가?
   - **Evidence-density clarity**: 각 메시지를 뒷받침할 자료(figure/data)가 또렷한가? 떠 있는 주장은?
   - **Constraint clarity**: 시간·분량·납품 포맷·표준 양식 제약이 또렷한가?
   각 차원 "명확 / 모호". '모호' 1개 이상이면 해당 challenge 라운드 발동.
6. **Challenge — 모호성 해소 라운드** (모호 차원에 대해 라운드를 돌린다, 각 1회 — scholar-deepen과 동형, 문서 도메인). 5번 판정에서 '모호'가 나온 차원이 다시 '명확'으로 풀릴 때까지 아래 라운드를 발동:
   - Round 4 "이 발표가 *없으면* 청중은 어떻게 되나? 꼭 있어야 하나?"
   - Round 6 "슬라이드를 절반으로 줄인다면 무엇을 버리나? 핵심 메시지 1개만?"
   - Round 8 "이 발표가 진짜 *무엇*인가? naming이 흔들리는 부분은?"
   - 이 라운드 루프의 soft limits(scholar-deepen 동형): round 3에서 4차원 전부 명확이면 early exit / round 10 soft warning(모호성이 빨리 안 풀린다 — 주제 재고) / round 20 hard cap(에스컬레이션).
7. 의도 명세 + topology + 4차원 판정 + analyzer 인벤토리를 게이트 0 으로 사용자에게 제시 → 확인 (모든 차원 명확 + 사람 확인 후 docs-plan).
</Steps>

<Output>
의도 명세: {포맷, 문서종류, 청중, 목적, 톤 프리셋, 입력 경로} + Round 0 topology + 4차원 정성 판정표(명확/모호) + 발동된 challenge 산출 + analyzer 의 소스 인벤토리.
다음 단계(docs-plan)가 그대로 받을 수 있는 형태.
</Output>
