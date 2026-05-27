---
name: docs-revise
description: |
  기존 문서를 verify PASS 받을 때까지 수정-검증 루프 — 작업중 문서를 "통과까지 고쳐줘". build 수정과
  verify 검증을 fresh 증거로 반복, 같은 결함 3회 반복이면 멈추고 보고(ralph 패턴의 문서판). 독립 진입.
  Triggers: 통과까지 고쳐, 문제 다 잡아줘, 계속 고쳐, 검증 통과할 때까지, 반복 수정,
  revise until pass, fix until verified, 수정 루프, 다 고쳐줘
---

# docs-revise — 수정-검증 루프 (ralph 문서판)

<Purpose>
기존 문서를 verify 가 PASS 줄 때까지 수정한다. doc-builder(수정)와 doc-verifier(검증)를 fresh 증거로 반복 — "do your best" 가 아니라 *통과 보장*. OMC ralph 의 문서판.
</Purpose>

<Use_When>
- 작업중/완성 문서를 "verify 통과까지 알아서 고쳐줘" 할 때
- docs-verify 가 FAIL 냈고 그 수정을 자동 루프로 돌리고 싶을 때
- 사용자가 "다 잡아줘", "통과할 때까지" 류
</Use_When>

<Do_Not_Use_When>
- 새 문서를 만드는 거면 → docs-build (또는 docs-pilot)
- 개선점 조언만 원하면 → docs-inspect (수정 안 함)
- citation-bound 문서면 → 자동 루프 금지 (내용 변조 위험), 단일 신중 수정
</Do_Not_Use_When>

<Execution_Policy>
- 각 반복: doc-builder 수정 → doc-verifier 가 fresh 증거로 검증 (이전 검증 재사용 금지).
- **scope 축소·placeholder 채움·검사 우회로 PASS 만들지 말 것** (ralph: no scope reduction, no deleting tests).
- builder 와 verifier 는 다른 lane — self-approval 금지.
- **같은 결함이 3회 반복되면 멈추고 보고** (fundamental issue — 무한 루프 차단).
- 합리적 최대 반복(기본 5회) 초과 시 멈추고 현황 보고.
</Execution_Policy>

<Steps>
1. 현재 상태 진단: `Task(subagent_type="oh-my-docs:doc-verifier", ...)` → FAIL 항목 목록.
2. **루프**:
   a. 수정: `Task(subagent_type="oh-my-docs:doc-builder", ...)` — FAIL 항목만 (versions/ 스냅샷은 큰 수정 시).
   b. 재검증: `Task(subagent_type="oh-my-docs:doc-verifier", ...)` — fresh 무결성 5/5 + 전수 정독.
   c. PASS 면 종료. FAIL 이면 같은 결함 반복 여부 확인:
      - 같은 결함 3회째 → 멈추고 "fundamental issue" 보고.
      - 아니면 (a)로.
3. PASS 또는 stop 조건에서 종료, 증거표 제시.
</Steps>

<Output>
PASS 받은 outputs/<doc>/current.<ext> + 반복 이력(각 회차 FAIL→수정 요지) + 최종 verify 증거표.
또는 stop 보고(같은 결함 3회 / 최대 반복 초과 + 남은 결함).
</Output>
