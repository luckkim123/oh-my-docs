---
name: docs-standardize
description: |
  여러 기존 문서에서 공통 표준 양식 규칙을 귀납 추출 — 폰트·컬러·여백·레이아웃 패턴을
  하나의 style spec 으로. 한 문서 추출(ppt-analyze)이 아니라 N개 문서에서 *공통 규칙*을 뽑아
  "우리 조직/랩 표준"을 만든다. round-trip 으로 spec 정확성 검증.
  Triggers: 양식 추출, 표준 양식, 우리 랩 발표 양식, 양식 규칙 뽑아, design system 추출,
  style spec, standardize, 공통 양식, 템플릿 규칙, 양식 통일
---

# docs-standardize — 표준 양식 추출 (2단계, 선택)

<Purpose>
여러 기존 문서를 분석해 *공통* 표준 양식 규칙(폰트·컬러 역할·여백·반복 레이아웃)을 귀납 추출, 하나의 style spec 으로 코드화한다. ppt-analyze 의 진화 — 한 문서가 아니라 N개에서 공통분모를 귀납.
</Purpose>

<Use_When>
- "우리 랩/조직 발표 양식 규칙을 뽑아줘" 류 — 여러 샘플에서 표준을 정의
- 새 문서를 기존 하우스 스타일에 맞춰 만들 때 (build 가 참조할 spec 생성)
</Use_When>

<Do_Not_Use_When>
- 참조할 기존 문서가 없을 때 → skip (build 가 기본 톤 프리셋 사용)
- 단일 문서 한 장만 분석하면 될 때 → doc-analyzer 직접 (귀납 불필요)
</Do_Not_Use_When>

<Gate>
**게이트 — 추출 범위 + round-trip.** 어떤 문서들을 표준 모집단으로 볼지 확정 → 추출 후
대표 1장 재생성 → 원본과 PNG 비교 ≥85% 일치. 미달이면 spec 보강.
</Gate>

<Steps>
1. 표준 모집단(여러 .pptx/.docx) 확정.
2. doc-analyzer 를 각 문서에 dispatch, 각각의 design system 추출:
   `Task(subagent_type="oh-my-docs:doc-analyzer", ...)`
3. 추출 결과들에서 **공통분모**(여러 문서에 반복되는 폰트/컬러/여백/레이아웃)를 귀납 → style spec.
4. round-trip 검증: spec 으로 대표 1장 재생성 → 원본과 비교. <85% 면 spec 보강.
5. style spec 을 게이트로 제시 → 확인.
</Steps>

<Output>
style spec (폰트·컬러 역할·여백·반복 레이아웃 패턴) — docs-build 가 "이 양식대로" 참조하는 데이터.
references/formats/<format>.md 의 함정 지식과 합쳐 builder 가 사용.
</Output>
