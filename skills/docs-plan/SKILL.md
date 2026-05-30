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

<Modes>
- **`--direct`** (기본): doc-planner 단일 위임으로 아웃라인 1개. 빠르고 가볍다.
- **`--consensus`**: doc-planner의 `<Consensus_RALPLAN_DR_Protocol>` 발동 — arc Options≥2를 거쳐 최종 1개로 수렴. analyzer→planner→[planner architect 책임]→inspector **순차**. `plan.md`(결정 과정) + 아웃라인(결정 결과) 2분리.

**`--consensus` 자동 발동 (Deliberate 트리거)**: 디펜스 · 심사 · 외부 공식 발표 중 하나라도 해당하면, `--direct`로 호출됐어도 사용자에게 "consensus 권장 — 진행?"을 1회 제안(자동 강제 아님, override 가능).
</Modes>

<Gate>
**게이트 1 — 구조 확정.** narrative arc + 전체 아웃라인을 사용자에게 제시. 산출물은 아직 없음 —
여기서 재배치가 가장 쌈. 승인 후 build. (`--consensus`면 plan.md+아웃라인 둘 다 제시.)
</Gate>

<Steps>
### `--direct` 경로 (기본)
1. doc-planner 를 dispatch (analyzer 인벤토리 + 톤 프리셋 전달):
   `Task(subagent_type="oh-my-docs:doc-planner", ...)`
2. planner 가 arc 선택 + 슬라이드별 목적·메시지·자산 아웃라인 산출.
3. 모든 필수 섹션이 배치됐고 포맷 density 한도(references/formats/<format>.md)를 지키는지 확인.
4. 아웃라인을 게이트 1 로 제시 → 승인.

### `--consensus` 경로 (순차 — 병렬 절대 금지)
> ⚠️ 아래는 MUST 순차 (3중 문구):
> ① (step-level) 각 step은 이전 step의 Task 결과를 await한 뒤에만 다음 Task를 발행. 두 Task를 같은 병렬 배치로 호출 안 함.
> ② (Important) analyzer → planner → [planner architect 책임] → inspector는 MUST 순차. 각 단계 결과를 await.
> ③ (CRITICAL) 컨트롤러의 await로만 순차 보장 (런타임 lock 없음). 동시 dispatch는 arc 불일치를 증폭.
1c. **analyzer** dispatch (인벤토리 보강 필요 시; 충분하면 기존 재사용). *끝난 후에만* 다음.
2c. **planner** dispatch (`--consensus` 지시): `<Consensus_RALPLAN_DR_Protocol>` 발동 — Principles + Drivers + arc Options≥2 + steelman + tradeoff + ADR + (Deliberate면) pre-mortem. 산출 = `plan.md` + 아웃라인.
3c. **[planner architect 책임]**: 별도 agent 아님 — planner가 steelman/antithesis로 이미 수행 (T1: doc-architect 신설 안 함).
4c. **inspector** dispatch (`doc-inspector`): plan.md+아웃라인을 formative 비평(critic 4기법, severity). PASS/FAIL 안 냄.
5c. **재리뷰 loop**: inspector가 critical/important 내면 planner 재위임(2c로) 후 재비평. 최대 5회. 5회 도달 시 best + "consensus not reached — 잔여 finding" 명시.
6c. **2분리 저장**: `plan.md`(RALPLAN-DR+ADR) + 아웃라인(Final 단일 arc). 게이트 1로 둘 다 제시.
</Steps>

<Output>
narrative arc + 슬라이드/섹션별 {목적, 핵심 메시지, 필요 자산} 아웃라인. docs-build 가 채울 설계도.
**`--consensus`면 추가**: `plan.md`(결정 과정 — RALPLAN-DR+ADR) + 재리뷰 회차(N/5) + consensus 도달 여부. plan.md와 아웃라인은 분리된 두 파일 (결정 과정 ≠ 결정 결과).
</Output>

<Consensus_Handoff>
> `--consensus` 순차 stage 간 전달 규약 (scholar-outline과 동형). **기본(SSOT) = .md 파일**, MCP는 *있으면 쓰는* 선택 가속 (결정1=C: OMD는 MCP 0건/standalone이 정체성).

**기본 경로 (.md — MCP 없이 동작)**:
- 각 consensus stage의 *구조화 산출*(planner의 steelman/antithesis/tradeoff/ADR, inspector의 finding 등)을 작업장 `.omd/<slug>/consensus/<stage>-<role>.md`로 쓴다. 예: `consensus/planner-adr.md`, `consensus/inspector-findings.md`. 구조화 헤더(role / stage / 작성 시점) + 본문.
- **rubber-stamp 방지 (기계적)**: 다음 stage는 *이전 role의 .md 파일이 디스크에 존재하는지 확인*한 뒤에만 진행. 부재면 진행 거부. 디렉토리 격리 = namespace 대체. consensus는 순차라 race 없음.
- `<slug>`·경로는 **작업 루트 상대** — 특정 사용자 절대경로 금지.

**선택(가속) MCP**: config gate `agents.sharedMemory.enabled` + shared_memory MCP 가용 시 동일 데이터를 `shared_memory_write(namespace="doc-consensus", key="<stage>-<role>", value={...})`로 미러 가능. ⚠️ **.md가 SSOT, MCP는 가속** — 부재 시 .md로 graceful degrade, 에러 아님.

**혼용 명확**: analyzer 인벤토리 등 비구조 산출은 기존 방식 그대로. consensus/ 디렉토리는 작업장 — 종료 시 T18 정리 대상.
</Consensus_Handoff>
