---
name: docs-plan
description: |
  문서 구조·아웃라인·스토리라인 설계 — narrative arc 선택 + 슬라이드/섹션별 목적·핵심메시지·필요
  자산 명세. 산출 전에 구조를 먼저 확정해 가장 싼 시점에 방향을 승인받는다. OMD 3단계.
  Triggers: 구조 짜줘, 아웃라인, 어떤 순서로, 발표 흐름, 스토리라인, 목차 설계,
  document outline, structure, narrative, 슬라이드 순서
---

# docs-plan — 구조 설계 (3단계)

<Purpose>
analyzer 인벤토리를 구체적 문서 구조로: narrative arc + 슬라이드/섹션별 목적·핵심 메시지·필요 자산. 산출 전에 구조를 확정해 *가장 싼 시점*(아무 산출물 없을 때)에 방향을 승인받는다.
</Purpose>

<Use_When>
- 의도가 명확하고 이제 어떤 순서·흐름으로 담을지 정할 때
- docs-pilot 의 설계 단계
</Use_When>

<Do_Not_Use_When>
- 구조가 이미 주어졌을 때 (기존 아웃라인 그대로) → docs-build 직행
- 무엇을 만들지 아직 흐릿할 때 → docs-intake 먼저
</Do_Not_Use_When>

<Gate>
**게이트 1 — 구조 확정.** narrative arc + 전체 아웃라인을 사용자에게 제시. 산출물은 아직 없음 —
여기서 재배치가 가장 쌈. 승인 후 build.
</Gate>

<Steps>
1. doc-planner 를 dispatch (analyzer 인벤토리 + 톤 프리셋 전달):
   `Task(subagent_type="oh-my-docs:doc-planner", ...)`
2. planner 가 arc 선택 + 슬라이드별 목적·메시지·자산 아웃라인 산출.
3. 모든 필수 섹션이 배치됐고 포맷 density 한도(references/formats/<format>.md)를 지키는지 확인.
4. 아웃라인을 게이트 1 로 제시 → 승인.
</Steps>

<Output>
narrative arc + 슬라이드/섹션별 {목적, 핵심 메시지, 필요 자산} 아웃라인. docs-build 가 채울 설계도.
</Output>
