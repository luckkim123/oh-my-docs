---
name: docs-pilot
description: |
  브리프 한 줄 → 완성 문서 전체 오케스트레이션. intake→standardize→plan→build→inspect→verify
  단계를 게이트마다 사용자 확인하며 엮는다. OMC autopilot 의 문서판. 자족적 진입점 —
  상위 메타-하네스가 "OMD 에 위임" 한 줄로 부를 수 있다.
  Triggers: 통째로 만들어줘, 처음부터 끝까지, 발표자료 다 만들어, 이 PDF로 디펜스 자료,
  docs pilot, document autopilot, 문서 자동, end to end 문서, 알아서 만들어
---

# docs-pilot — 산출 오케스트레이터

<Purpose>
브리프에서 완성 문서까지 전 단계(의중파악 → 표준추출 → 설계 → 산출 → 검토 → 검증)를 자동 조율한다. 사용자는 *무엇이 필요한지*만 말하고, *어떤 도구로·어떤 구조로·어떻게 검증할지*는 하네스가 정한다. 단, 위험(통째 재작업)이 크므로 게이트마다 확인 — 완전 자율 아님.
</Purpose>

<Use_When>
- "이 PDF로 디펜스 자료 통째로 만들어줘" 류 end-to-end 요청
- 상위 메타-하네스(omha)가 문서 작업을 OMD 에 위임할 때 (자족 진입점)
</Use_When>

<Do_Not_Use_When>
- 한 단계만 필요할 때 → 해당 단계 스킬 직접 (docs-inspect 만, docs-build 만 등)
- citation-bound 문서(논문 등) → 병렬화 금지, builder 단독 신중 처리 (hallucination 위험)
</Do_Not_Use_When>

<Execution_Policy>
- 각 단계는 fresh subagent 로 dispatch — 컨트롤러 컨텍스트 보호.
- 게이트 0~3 에서 사용자 확인 후 다음 단계. 위험 = 통째 재작업이므로 확인 생략 안 함.
- inspect(형성)와 verify(총괄)는 builder 와 다른 lane — self-approval 금지.
- FAIL 시 docs-build 로 되돌려 수정 루프 (최대 합리적 횟수, 같은 결함 3회 반복이면 멈추고 보고).
- 어느 단계든 명세가 이미 충족되면 skip (아래 Steps 의 skip 조건).
</Execution_Policy>

<Steps>
1. **docs-intake** → doc-analyzer dispatch: 의중 크리스탈화 + 입력 인벤토리.
   - *명세가 이미 또렷하면(포맷·청중·톤 다 정해짐)* skip.            ──[게이트 0: 의도]
2. **docs-standardize** → doc-analyzer dispatch: 참조 문서 있으면 공통 표준 추출.
   - *참조 문서 없으면* skip (기본 톤 프리셋 사용).
3. **docs-plan** → doc-planner dispatch: narrative arc + 아웃라인.       ──[게이트 1: 구조]
4. **docs-build** → doc-builder dispatch: 카드 보고 엔진 산출(수식 포함). ──[게이트 2: 콘텐츠]
5. **docs-inspect** → doc-inspector dispatch: PPTEval 3축 형성적 비평.
   - build 수정 루프와 병렬 (spec≠quality 분리).
6. **docs-verify** → doc-verifier dispatch: 무결성 5/5 + 전수 정독.       ──[게이트 3: 최종]
   - FAIL → 4번(build)으로 되돌림.
</Steps>

<Output>
outputs/<doc>/current.<ext> (PASS 받은 최종본) + versions/ 이력 + verify 증거표.
각 단계 산출이 다음 단계 입력으로 연결됨.
</Output>

<Self_Sufficiency>
이 스킬은 자족적 진입점이다. 상위 메타-하네스(omha)가 문서 작업을 "OMD docs-pilot 에 위임" 한 줄로 부를 수 있도록, 외부 컨텍스트 없이 brief 만으로 전 단계를 완주한다.
</Self_Sufficiency>
