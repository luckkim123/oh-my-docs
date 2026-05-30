# OMC Backport Analysis — oh-my-docs (omd)

omd 의 intake 모호성 게이트·consensus 레이어·inspector critic 기법·런타임 누적(wiki/notepad/
verifier 토큰)은 **oh-my-claudecode (OMC)** 의 검증된 패턴을 문서/슬라이드 도메인으로 옮겨온
것이다. OMC 가 업데이트되면 *무엇이 바뀌었고 omd 를 갱신해야 하는지* 판단할 영속 기준이
필요하다. OMC 는 CHANGELOG 가 없고(GitHub commit/release 만 존재) 개별 파일 버전도 없으므로,
"diff 기준"을 이 문서가 자체 보관한다.

> **이 문서는 배포 plugin 의 references/ 라 개인 환경에 비의존이다.** OMC 경로는 *공개 plugin
> 내부 구조*(상대 표현)로만 적는다. 특정 머신의 절대경로·작업 메모·사용자 조직 체계는 박지 않는다.

---

## §1. OMC 4.14.4 구조 스냅샷 — backport 원천 컴포넌트

OMC plugin 은 **이중 구조**다: `skill-bodies/<name>/SKILL.md` 가 전체 로직이고,
`skills/<name>/SKILL.md` 는 시작 컨텍스트를 가볍게 유지하기 위한 *compact 참조 shim*
(본문을 `skill-bodies/` 에서 로드). backport 의 원천은 항상 `skill-bodies/` 쪽이다.

| 원천 (OMC 4.14.4 내부 경로) | 무엇을 가져왔나 |
|:---|:---|
| `skill-bodies/deep-interview/SKILL.md` | Round 0 topology · 차원별 모호성 판정 · challenge agents(contrarian/simplifier/ontologist) · soft limits · 3-point injection → **docs-intake** 의 모호성 강화 골격 |
| `skill-bodies/plan/SKILL.md`, `skill-bodies/ralplan/SKILL.md` | RALPLAN-DR consensus(Principles/Drivers/Options≥2/steelman/tradeoff/ADR) · 순차 강제(병렬 금지) 프롬프트 규율 → **doc-planner** + **docs-plan --consensus** |
| `skill-bodies/autopilot/SKILL.md` | brief→완성 단계 오케스트레이션 + 게이트 골격 → **docs-pilot** |
| `skill-bodies/ralph/SKILL.md` | 결함=PRD·passes:true 게이트까지 fix/verify 루프·no scope reduction → **docs-revise**(이미 보유, 이번 backport 에선 미변경) |
| `agents/analyst.md` | 사전 진단·요구 분석 사상 → docs-intake 의 의중 크리스탈화 |
| `agents/architect.md` | steelman/antithesis/tradeoff → **doc-planner 에 흡수**(별도 agent 신설 안 함) |
| `agents/planner.md` | narrative arc·아웃라인 → doc-planner |
| `agents/critic.md` | pre-commitment · assumption(VERIFIED/REASONABLE/FRAGILE) · pre-mortem · self-audit → **doc-inspector 의 4기법** |
| OMC MCP 도구 서버 (`wiki_*`/`notepad_*`/`shared_memory_*`/`state_*`) | 누적·압축생존·핸드오프 *사상*. ⚠️ omd 는 **.md degrade 가 기본**이고 MCP 는 선택 가속 — Node MCP 를 새로 넣지 않는다 |

---

## §2. 분석 기준 버전 + diff 기준

- **분석 기준 snapshot = OMC 4.14.4.** 이 문서가 backport 원천을 읽을 때 본 OMC 버전이다
  (당시 plugin 의 `package.json`·`.claude-plugin/plugin.json`·`.claude-plugin/marketplace.json`
  세 곳 모두 `"version": "4.14.4"`). **이것은 *분석 시점의 스냅샷*이지 런타임 핀이 아니다** —
  `~/.claude/settings.json` 의 omc marketplace 선언(`repo: Yeachan-Heo/oh-my-claudecode`)에는
  버전·commit-SHA 가 없어 **OMC 는 항상 marketplace 최신을 자동 추종**한다. oms/omd 어디에도
  OMC 를 특정 버전으로 묶는 핀은 없다. 따라서 OMC 업그레이드에 별도 작업이 필요 없고,
  아래 diff 기준은 *backport 채택/제외 결정이 여전히 유효한지* 재검토하기 위한 것일 뿐이다.
- **diff 기준**: OMC 는 CHANGELOG 가 없다(GitHub commit/release 만). 다음 OMC 업데이트 시,
  위 §1 원천 파일들(`skill-bodies/{deep-interview,plan,ralplan,autopilot,ralph}/SKILL.md`,
  `agents/{analyst,architect,planner,critic}.md`)의 diff 를 직접 보고 omd 갱신 여부를 판단한다.
- 판단 규칙: OMC 업데이트가 **§3 의 *채택* 영역**을 바꾸면 → 대응 backport 갱신 검토.
  **§3 의 *제외* 영역**을 새로 건드리면 → 제외 결정이 여전히 유효한지 재검토.

---

## §3. 채택·제외 매핑 (내부 backport 작업 ID = Tn)

> Tn 은 이 repo 의 내부 backport 작업 식별자(니모닉)다. 각 행은 *무엇이 바뀌었나*로
> 자족 기술하므로 외부 plan 문서 없이도 읽힌다. oms(논문)와 동형이되 도메인만 다르다.

### 채택 (adopt)

| Tn | OMC 패턴 | omd 적용 (실제 변경) |
|:---|:---|:---|
| T1 | deep-interview/ralplan 의 단계 경계 | intake↔plan↔consensus 경계 규약. doc-architect·docs-plan-consensus **신설 안 함**(doc-planner·docs-plan 모드로 흡수) |
| T3 | critic 4기법 + severity | `agents/doc-inspector.md` 에 **severity 축 선행 도입**(1차 severity / 2차 rank / confidence 는 severity 축) 후 pre-commitment·assumption(V/R/F)·pre-mortem·self-audit 를 PPTEval 3축 *안에* 삽입. **rank 는 omd 고유**(슬라이드 다수 finding 정렬) — oms 와의 동형은 "severity 축 + 4기법"까지 |
| T6 | ralplan RALPLAN-DR + architect | `agents/doc-planner.md` 에 RALPLAN-DR + steelman + ADR. `'One arc only'` 세 조항은 *삭제 안 하고* mode-aware 편집(--direct=단수 arc 보존, --consensus=plan.md 에서 Options≥2→최종 단일 arc 수렴). `skills/docs-plan/SKILL.md` --consensus 모드 |
| T7 | shared_memory 핸드오프 | consensus stage 간 전달 = `<slug>/consensus/*.md` 파일이 **기본**, MCP 는 선택 미러(부재 시 .md degrade) |
| T9 | deep-interview 게이트 | `skills/docs-intake/SKILL.md` 에 게이트 0(5필드 Socratic) 유지 + Round 0 topology + 4차원 **정성** 판정(Audience/Message/Evidence-density/Constraint, 수치화 0) + challenge 3종 + 모호성 해소 라운드 루프 |
| T8b | autopilot wiring | `skills/docs-pilot/SKILL.md` `<Steps>` 에 docs-plan --consensus 분기 삽입(Deliberate 트리거=디펜스/심사/외부공식발표) — 엔진이 autopilot 경로에서 실제 발동(죽은 코드 방지) |
| T10 | wiki 누적 | `references/wiki/*.md` + 결정론적 grep 이 **기본**, `wiki_query(category)` 는 추상 함수(미래 MCP 교체점). docs-standardize 가 귀납한 style spec 을 "랩 표준"으로 compound |
| T11 | notepad 압축생존 | docs-pilot 진입 시 `.omd/notepad.md` `## Priority Context` 섹션에 원본 in-place 금지 + 게이트 기록(.md 기본) |
| T12 | verifier request-id | `agents/doc-verifier.md` 에 스냅샷 상관 토큰(current.<ext> mtime·CRC + 결함ID) — multi-round revise 의 stale-PASS 재사용 차단 |
| T14 | (omd 자체 라우팅) | `hooks/route_emit.py` STAGE 카탈로그에 `revise` 토큰 추가(docs-revise 실재하나 누락이던 것 수정) + Deliberate→`--consensus` 근거 단서. 회귀 테스트 `tests/test_route_emit.py` 신설(omd 최초 tests/) |
| T15 | state 경로 | 작업장 = `.omd/<slug>/` 고정(`.omd/specs`·`sessions/{sid}` 미검증 세그먼트 제거). 30s state-MCP 트랩은 *미래 대비 메모만* |
| T16 | (계약 이력) | `CHANGELOG.md` 신설 — commit-SHA 버저닝 유지하되 hook 계약 변경을 명문 기록(oms [0.1.1] 톤 통일) |

### 제외 (exclude — 사유 포함)

| OMC 패턴 | 제외 사유 |
|:---|:---|
| doc-architect / docs-plan-consensus 류 **신설** | doc-planner·docs-plan 모드와 중복 → 확장으로 흡수 |
| **구조-regression 조항(T13)** | omd 미적용 — docs-revise 는 이미 acceptance(전수 PNG 정독 + "직전 회차 FAIL 결함 재현 안 됨")로 방어 충분. oms(scholar-revise)에만 비대칭 적용 |
| **state MCP 실호출** | 단일·순차 철학에 과잉. notepad(.md) 가 압축생존 더 잘함. 30s 트랩은 문서화만 |
| persistent-mode **Stop-hook 강제** | freeze 위험, revise 루프로 충분. 보류 |
| **ambiguity 수치화**(가중합·threshold·stability_ratio) | 정성 게이트 채택 — magic number 근거 약함 |
| **multi-perspective / realist / adversarial escalation** | pre-mortem·self-audit 와 중복, inspector formative "stop when read & ranked" 와 충돌(formative↔verify 경계 흐림) |
| 코드 전용 런타임 15+ (comment-checker·code-simplifier·ast/lsp·python_repl·ultragoal·loop_authority 등) | 도메인 무관 |
| **임베딩 검색** | wiki 누적이 환각을 끌어오지 않도록 결정론적 매칭만(현재도 미래도 영구 금지) |

---

**Analysis snapshot**: OMC 4.14.4 (런타임 핀 아님 — marketplace 최신 자동 추종, §2) · **isomorphic sibling**: oh-my-scholar `references/omc-backport-analysis.md`(논문 도메인)
