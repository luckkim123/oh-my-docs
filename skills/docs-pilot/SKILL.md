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
- **진입 시 priority 컨텍스트 기록 (압축 생존)**: 파이프라인 시작 시 `.omd/notepad.md`의 `## Priority Context` 섹션에 치명 제약을 적는다 — "원본 in-place 수정 금지 / 최종본은 `outputs/<slug>/current.<ext>` 하나, 버전·중간물은 `.omd/<slug>/` / 현재 게이트 n + slug". 긴 파이프라인에서 컨텍스트가 압축돼도 원본 파괴 방지와 게이트 위치가 항상 복원되도록.
  - **.md가 기본**: 직접 `.omd/notepad.md`에 write/append. notepad MCP 가용 시 `notepad_write_priority(...)`로 미러 가능(같은 .md 대상, 선택 가속) — 부재해도 .md write로 동일 동작, 에러 아님.
- 작업장 경로는 **`.omd/<slug>/`** 고정 (검증된 실재 경로; `.omd/specs`·`sessions/{sid}` 같은 미검증 하위 세그먼트는 박지 않는다).
  - ⚠️ **30s 트랩 (향후 state MCP 도입 시에만 — 지금은 미적용)**: state MCP를 쓰게 되면 단계 핸드오프 *직전*에 `state_clear`를 호출하지 말 것(30s간 모든 모드의 stop-hook이 비활성화돼 루프가 조용히 끊긴다). 비종료 핸드오프는 `state_write(active=false)`로, `state_clear`는 *terminal(파이프라인 완전 종료)에서만*. **현재는 state MCP를 실호출하지 않으므로(.md/`.omd/` 파일이 기본) 순수 미래 대비 메모.**
</Execution_Policy>

<Steps>
1. **docs-intake** → doc-analyzer dispatch: 의중 크리스탈화 + 입력 인벤토리 + Round 0 topology + 4차원 정성 모호성 판정(Audience/Message/Evidence-density/Constraint).
   - *명세가 이미 또렷하고(포맷·청중·톤 다 정해짐) 4차원 전부 명확하면* skip.   ──[게이트 0: 의도]
2. **docs-standardize** → doc-analyzer dispatch: 참조 문서 있으면 공통 표준 추출.
   - *참조 문서 없으면* skip (기본 톤 프리셋 사용).
3. **docs-plan** → doc-planner dispatch: narrative arc + 아웃라인.
   - **모드 분기**: Deliberate 트리거(디펜스 / 심사 / 외부 공식 발표)면 `docs-plan --consensus`(RALPLAN-DR 4-agent 순차), 아니면 `--direct`. 자동 판정 + 사용자 override.  ──[게이트 1: 구조. consensus면 plan.md+아웃라인 둘 다 제시]
4. **docs-build** → doc-builder dispatch: 카드 보고 엔진 산출(수식 포함). ──[게이트 2: 콘텐츠]
5. **docs-inspect** → doc-inspector dispatch: PPTEval 3축 형성적 비평.
   - build 수정 루프와 병렬 (spec≠quality 분리).
6. **docs-verify** → doc-verifier dispatch: 무결성 5/5 + 전수 정독.       ──[게이트 3: 최종]
   - FAIL → 4번(build)으로 되돌림.
7. **terminal cleanup** (verify PASS + 게이트 3 사용자 최종 확인 후, 또는 사용자가 "정리해줘"/"작업 끝" 명시 시):
   - `.omd/<slug>/`의 정리 대상 **집계**(크기·개수): `renders/`·`gen-image/`·`tmp/` 전부 + `versions/`의 최신 1개·사용자 지정 이정표를 **제외한** 구버전. 이정표 선택을 위해 versions 목록을 사용자에게 보여준다.
   - **AskUserQuestion [정리 / 유지]** — 자동 삭제 절대 없음, 기본값 보수적(유지).
   - "정리" 선택 시 → **복구 가능 경로로 삭제**(영구 `rm` 금지): macOS `trash`(없으면 `~/.Trash` 이동) / Linux `gio trash`·`trash-cli` / 휴지통 없는 환경(CI·컨테이너)은 "영구 삭제" 사용자 재확인 후에만.
   - ⚠️ `outputs/<slug>/current.<ext>`(사용자 자산)는 집계·삭제 대상에서 **제외** — 언급만. 상세 절차는 `references/output-layout.md` §5.

> **`--from <stage>` 진입점**: 중간 단계부터 시작 가능 — `intake|standardize|plan|build|inspect|verify`. intake의 topology/모호성 판정은 `--from intake`에 포함.
</Steps>

<Output>
사용자가 보는 최종본은 `outputs/<slug>/current.<ext>`(PASS 받은 단 하나) + 선택적 verify 증거표.
버전 이력·렌더·중간물은 작업장 `.omd/<slug>/`(`versions/`·`renders/`·`gen-image/`·`tmp/`)에 — 경로 규약은 `references/output-layout.md`가 SSOT. 각 단계 산출이 다음 단계 입력으로 연결됨.
</Output>

<Self_Sufficiency>
이 스킬은 자족적 진입점이다. 상위 메타-하네스(omha)가 문서 작업을 "OMD docs-pilot 에 위임" 한 줄로 부를 수 있도록, 외부 컨텍스트 없이 brief 만으로 전 단계를 완주한다.
</Self_Sufficiency>
