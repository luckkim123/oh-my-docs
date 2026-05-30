# Changelog

All notable changes to oh-my-docs (omd).

> **버저닝 방침**: omd 는 의도적으로 **commit-SHA 버저닝**을 쓴다(개별 릴리스 번호 없음).
> 이 파일은 *계약(contract) 변경 이력*만 추적한다 — hook 의 emit 포맷처럼 다른
> 컴포넌트(omha·세션 LLM)가 의존하는 표면이 바뀌면 여기 기록한다. 일반 콘텐츠
> 변경은 git 로그가 SSOT. OMS(oh-my-scholar)의 CHANGELOG 톤과 통일.

## [Unreleased]

### Changed
- **라우팅 hook 계약 확장** (`hooks/route_emit.py`, UserPromptSubmit): STAGE 카탈로그에
  `revise` 토큰 추가 — `docs-revise` 스킬이 실재하나 STAGE 목록에서 누락돼 있던 것을 수정
  (`intake|standardize|plan|build|inspect|verify|revise|docs-pilot`). 또한 Deliberate
  (디펜스·심사·외부 공식 발표) 트리거 시 `docs-plan --consensus`(RALPLAN-DR) 발동을 한 줄
  근거에 밝히라는 단서를 주입. stdlib only·fail-open 패턴 유지.

### Added
- **라우팅 hook 회귀 테스트** (`tests/test_route_emit.py`, 신설): omd 는 그동안 `tests/`가
  없었으나 hook 은 *계약*이라 변경 시 회귀 검증이 필요 → 9건 신설(UserPromptSubmit emit·
  STAGE contract·8단계 열거(revise 포함)·3포맷 열거·format 카드 권위·`--consensus` 근거·
  레이블 충돌 없음(STAGE(docs)↔STAGE(paper)↔ROUTE)·stdlib only·fail-open).
- **OMC backport 분석 문서** (`references/omc-backport-analysis.md`, 신설): deepen·consensus·
  critic 4기법 등이 OMC 4.14.4 의 무엇에서 왔고 무엇을 제외했는지 영속 기록 — OMC 업데이트 시
  갱신 판단 기준.

### Verification
- `pytest tests/` — 9 passed (route_emit 회귀).
- 두 hook 모두 `python3 -c "import ast; ast.parse(...)"` 통과 + 실행 시 valid JSON emit
  (`revise`·`--consensus` 포함 확인).
