# omd 확장 프로그램 설계 — 문서 하네스 전면 최신화 (R1–R4)

| 필드 | 값 |
|:---|:---|
| **Date** | 2026-07-11 |
| **Subject harness** | oh-my-docs (omd) — 현재 미버전(plugin.json에 version 필드 없음), `main` @ 5018c27 |
| **Reference harness** | oh-my-claudecode v4.15.2 — claudebase `docs/reference/omc-deep-analysis-v4.15.2/` (19챕터 + `gaps/oh-my-docs.md`) 기준 |
| **Inputs** | ① OMC deep-analysis 19챕터 + omd 전용 갭 분석(우선순위 후보 7개) ② omx 백포트 선례(alignment-audit → program-design → r1~r3 plans, `~/oh-my-experiments/docs/`) ③ omd 저장소 전수조사(스킬 12·에이전트 5·훅 2·포맷 카드 5·테스트 4 전량 정독 + pytest 실측) ④ 외부 조사 4-facet(SSG 지형 / GitHub 문서 표준 / 문서 품질 프레임워크 / AI 문서도구 선행 사례) — 출처는 §9 |
| **Method** | 병렬 리서치 에이전트 7개(저장소 정독 3 + document-specialist 웹 4) → 세션 종합 → critic(opus) 독립 검토 |
| **Review** | ① critic(opus) 2026-07-11 — "수정 후 승인" (blocker 0), 발견 M1·M2·m1–m5 반영. ② ultracode 심층 감사 — 6클러스터 33 에이전트, 발견 26건 중 확정 22 + 완전성 비평 6, 전량 반영 (부록 A). ③ ultracode OMC 채굴 — 8클러스터×2라운드 70 에이전트, 후보 52건 중 교차 확정 10건 독립 채택 + 4건 기존 항목 흡수 + 1건 R2 결정 항목 (§3.4, 부록 B) |
| **Scope** | 프로그램 프레임(R1–R4 릴리스 트레인 + 잠금 결정 D1–D8) + 릴리스별 컴포넌트 설계. 태스크 단위 TDD 분해는 릴리스별 plan 문서(`docs/superpowers/plans/YYYY-MM-DD-omd-vX.Y.Z-rN.md`)가 담당 — 이 문서는 spec 층. |

---

## 0. Executive summary

omd를 "오피스 4종(pptx/docx/xlsx/hwpx) 생성기"에서 **"모든 문서 장르를 전문가 수준으로 생산하는 하네스"**로 확장한다. 신규 장르는 두 가지: **repo-docs**(README/CHANGELOG/community health files — GitHub 저장소 문서 세트)와 **site**(MkDocs+Material 기반 정적 문서 사이트). 동시에 OMC v4.15.2 갭 분석이 지적한 **"선언된 규칙을 강제하는 코드 게이트 부재"** 7건을 백포트해 기존 파이프라인의 보증 수준을 올린다. 프로그램은 4개 릴리스(R1 위생+게이트 → R2 repo-docs → R3 site → R4 지식 수명주기)로 나누며, 배포 범용성(개인 식별자 0, stdlib-only 훅)과 wiki 기반 사용자 특화(FORM만 학습, content 불가침)라는 기존 불변식을 전 릴리스에 걸쳐 유지한다.

경쟁 지형 근거(§9 facet 4): Mintlify·GitBook·readme-ai·Swimm 등 상용/오픈소스 AI 문서 도구 전부가 (a) 기계적 품질 게이트 부재, (b) 개인화가 정적 룰 파일 수준, (c) 클라우드 종속이라는 공통 갭을 갖는다. omd의 doc-verifier(fresh-evidence PASS/FAIL) + 2계층 wiki 자동 특화 + 완전 로컬 실행은 이 3대 갭에 정확히 대응하므로, 이 확장은 기존 강점을 새 장르로 일반화하는 작업이지 새 정체성을 만드는 작업이 아니다.

---

## 1. 배경과 목표

### 1.1 확장 비전

| 축 | 현재 | 목표 |
|:---|:---|:---|
| 포맷 커버리지 | pptx/docx/xlsx/hwpx (+pdf 입력측) | + **repo-docs**(README·CHANGELOG·CONTRIBUTING·SECURITY·이슈/PR 템플릿·CODEOWNERS), + **site**(MkDocs+Material 정적 사이트) |
| 품질 보증 | 오피스 포맷: 렌더 정독 + integrity 5-check + shape assertion | 텍스트 장르: **결정론적 exit-code 체인**(`mkdocs build --strict`, markdownlint, 링크 체크) + fresh-read — "코드가 돈다 ≠ 검증됐다" 원칙의 텍스트판 |
| 규칙 강제 | prose 규칙 + advisory 리마인더 | + **코드 게이트 7종 백포트**(Stop-guard 핸드셰이크, model-tier 가드, 엔진 버전 고정 등) |
| 학습/특화 | 2계층 wiki + learned.md(capture 경로 부재로 관찰 축적 0 — 빈 원장 자체는 설계상 정상 초기 상태) | wiki lint·notepad pruning·capture 자동화로 **"쓸수록 특화" 루프를 실제로 돌게** 만듦 |

### 1.2 두 원칙 (요청 사양)

1. **배포 범용성**: omd는 배포되는 플러그인이다. 코어에 개인 절대경로·프로젝트 고유명사·머신 특정 값이 섞이면 안 되며, 이를 prose가 아닌 **pytest로 기계화**한다(D8, omx `test_distribution_axiom.py` 선례).
2. **wiki 기반 점진 특화**: 범용 출발점이 사용자의 사용 이력으로 특화되는 유일한 경로는 `.omd/wiki/` + `learned.md` → 사람 게이트 승격이다. 신규 텍스트 장르에서도 **FORM(문체·구조·배지 스타일·changelog 컨벤션)만 학습하고 content(프로젝트 사실·API 이름·수치)는 영구 불가침**(anti-pattern F의 확장, D7).

---

## 2. 현재 상태 진단 (2026-07-11 실측)

### 2.1 실측 결함 — 즉시 수리 대상 (R1)

pytest 실측: **2 failed, 31 passed** (2026-07-11, main @ 5018c27).

| # | 결함 | 근거 | 심각도 |
|:--|:---|:---|:---|
| H1 | `docs-pdf` 스킬이 plugin.json에 미등록 → `test_plugin_integrity.py::test_every_skill_dir_is_registered` **FAIL** | skills/ 12개 vs `.claude-plugin/plugin.json:7-19` 11개 등록 | 높음 — 이 테스트는 2026-05-31 docs-learn 누락 사고 후 만든 가드인데 정확히 같은 사고가 재발한 상태 |
| H2 | docs-pilot에서 "식별자 스크럽"(cross-project confidentiality gate) 문구 소실 → `test_wiki_two_level.py::test_cross_project_confidentiality_gate_present` **FAIL** | tests/test_wiki_two_level.py:110 | 높음 — 기밀 격리 계약의 문서 표현 회귀 |
| H3 | plugin.json에 **version 필드 자체가 없음** — 버전 규율 미확립, CHANGELOG는 `[Unreleased]`뿐 | `.claude-plugin/plugin.json` | 높음 — 릴리스 트레인의 전제 |
| H4 | `docs_verify_emit.py` DOC_EXTS가 선언만 되고 미사용(죽은 상수), xlsx도 빠져 있음 | hooks/docs_verify_emit.py:25 | 중간 |
| H5 | **pdf 라우팅 층위 미결정** — pdf는 생성 포맷이 아니라 입력(docs-pdf)·변환 타깃(docs-convert) 층위다. FORMAT 슬롯 단순 편입은 "pdf를 생성한다"는 오신호이므로, 수리가 아니라 층위 결정(별도 표기 vs 편입)이 필요 | hooks/route_emit.py:24, references/formats/pdf.md:1, skills/docs-convert/SKILL.md:14,30 | 중간 — 결정 항목 |
| H6 | README "Status (2026-05-31) MVP: pptx pilot" — 이후의 docx/xlsx/hwpx 카드 완성·pdf 카드·2계층 wiki를 미반영. CHANGELOG도 최근 작업 기록 0 | README.md:41-43 | 중간 |
| H7 | references/themes/ 10개 프리셋이 docs-build/standardize 스킬 본문에 미연결 | references/themes/README.md | 낮음 |

### 2.2 확장 마찰 지점 — 텍스트 장르가 기존 전제와 충돌하는 곳 (R2에서 일반화)

| # | 마찰 | 근거 | 해소 방향 |
|:--|:---|:---|:---|
| F1 | `outputs/<slug>/current.<ext>` **단일 파일 불변식**이 다중 파일 산출물(사이트 트리, README+CHANGELOG 세트)과 구조적 불일치 | references/output-layout.md:22 | artifact-set 일반화 (D4) |
| F2 | `docs_verify_emit.py`가 **Bash 빌드 명령만** 트리거 — md 계열은 Edit/Write로 편집되므로 훅이 아예 안 발화. 훅 주석 스스로 "oms는 .tex/.bib에 Edit\|Write 방식"이라고 밝힘 | hooks/docs_verify_emit.py:28-32 | md 계열은 oms 모델(Edit\|Write PostToolUse) 채택 (D5) |
| F3 | doc-verifier의 integrity 5-check(zip CRC 등)와 Shape Assertion이 OOXML/pptx 전제 하드코딩 | agents/doc-verifier.md:21,44,84-99 | 포맷 조건부 분기 — 카드가 verify 경로를 정의 |
| F4 | PPTEval 루브릭(3축)은 "페이지 렌더" 기반 — 텍스트/사이트 문서에 성립 안 함 | references/rubrics/ppteval.md:1-5 (출처 명기부 — PPTAgent arXiv, 슬라이드 평가 전용) | 장르별 신규 루브릭 (repo-docs·site) |
| F5 | route_emit.py CHECKPOINT 본문에 포맷 열거가 **2곳**(FORMAT 슬롯 :24 + STAGE 토큰 줄 :40) 하드코딩. 이 본문 문자열을 assert하는 테스트가 `test_context_lists_formats` 하나가 아니라 **route_emit 테스트 전반**(`test_context_states_stage_emit_contract` 등)이므로 포맷 추가 시 전부 재검증 대상 | hooks/route_emit.py:23-24,40, tests/test_route_emit.py:42-47,76-83,100-107 | 포맷 토큰 확장 + CHECKPOINT 텍스트 회귀를 plan 태스크로 명시 |
| F6 | docs-standardize의 "양식 추출" 게이트가 pptx placeholder map + PNG round-trip(≥85% 일치) 전제 — repo-docs의 양식(섹션 순서·voice·배지 컨벤션)은 렌더할 페이지가 없어 절차가 성립 안 함 | skills/docs-standardize/SKILL.md:29,33-34,42 | §4.4-6: 포맷 조건부 분기 — 텍스트 장르는 카드 표준 컨벤션 checklist 일치 확인(새 계량 메커니즘 발명 없이 D3 프레임 재사용) |
| F7 | **파이프라인 앞단 4파일(docs-intake·docs-plan SKILL.md + doc-planner·doc-analyzer.md)이 발표 장르 하드코딩** — "slides", "narrative arc", "tone preset (defense/conference/lecture)"가 계약의 골자라 repo-docs(섹션 프리셋이 계약)·site(Diátaxis가 프레임)는 Gate 0/1을 통과할 방법이 없음. 뒷단만 일반화하면 신규 장르가 파이프라인 진입 자체를 못 함 | skills/docs-intake/SKILL.md Steps 4-6, skills/docs-plan/SKILL.md, agents/doc-planner.md, agents/doc-analyzer.md | §4.4-8: 앞단 어휘를 "카드가 장르별 intake 질문·구조 프레임을 정의"로 일반화 |
| F8 | references/themes/ 10 프리셋이 오피스 색·폰트 팔레트 전용인데 "no reference → default tone preset" 폴백의 유일한 구체물 — repo-docs(팔레트 무의미, GitHub이 렌더)·site(mkdocs-material `palette:` 스키마로 형식이 다름)에서 폴백이 오피스 테마로 잘못 귀결 | references/themes/README.md | §4.4-13: themes는 오피스 전용 명시, 텍스트 장르 폴백은 카드가 정의(repo-docs=섹션 프리셋, site=material palette 스키마) |

### 2.3 그대로 재사용 가능한 것 (확장의 지렛대)

stage 파이프라인(intake→standardize→plan→build→inspect→verify→revise)·human gate 철학·`.omd/<slug>/` 작업영역 vs `outputs/` 분리·"카드가 SSOT" 원칙·author≠reviewer 에이전트 분리(doc-verifier self-approval triple ban)·2계층 wiki — 전부 포맷 불가지론적이라 신규 장르에 무수정 재사용. **이것이 이 프로그램의 핵심 전제: 새 포맷 = 새 스킬이 아니라 새 카드다.**

---

## 3. Audit synthesis — OMC v4.15.2 백포트 판정

입력: claudebase `gaps/oh-my-docs.md`가 이미 stdlib-only·fail-open·`.omd/`-relative 조건으로 선별한 우선순위 후보 7개. 아래 판정은 그 후보를 릴리스에 배정하고, omx 선례(§9 ②)에서 추가 채택분을 더한 것이다.

### 3.1 gaps 후보 7개 판정

| # | 후보 | 판정 | 릴리스 | 비고 |
|:--|:---|:---|:---|:---|
| G1 | **docs-verify Stop-hook arm/confirm/enforce 핸드셰이크** — doc-build 감지 시 `.omd/<slug>/.verify-pending` 센티널, Stop 시 fresh-verify 없으면 additionalContext 리마인드 | ADOPT | **R1** | gaps 명시 최우선. omd 1위 실패모드("fresh render 없이 done") 직격. advisory·fail-open 유지, `decision:block` 금지(D6). 심층 감사 보강 3건 — ① Stop 훅은 세션 상태 저장소 없이 `.omd/*/.verify-pending` 전수 glob 스캔으로 미해소 센티널을 나열(다중 slug 시나리오, HK-1) ② 센티널은 mtime을 담아 이전 세션 이월분을 "이월된 미해결 verify"로 구분 표시하되 TTL 자동 만료는 비채택 — 낡은 방치물을 침묵시키면 G1이 막으려는 실패모드를 재도입(HK-4) ③ 리마인드 문구에 "advisory이며 무시하고 진행 가능(verify를 나중에 해도 무방)"을 명시해 의도적 verify 유예를 문구로 흡수 — 자연어 의도 파싱은 stdlib 훅 범위 밖이므로 명시적 배제(HK-2) |
| G2 | notepad 3-tier(Priority/Working/Manual) pruning + PreCompact 재주입 | ADOPT | R4 | `hooks/precompact_reinject.py` (stdlib) |
| G3 | wiki 기계적 lint(orphan/stale/broken-ref/oversized) report-only | ADAPT | R4 | omx `wiki/lint.py`의 near-duplicate(Jaccard≥0.5) 체크 추가 차용. hook 아닌 script — docs-learn이 호출 |
| G4 | **agent model-tier 가드** — `Task(subagent_type="oh-my-docs:...")` 시 agent .md frontmatter의 `model:`과 요청 모델 불일치를 advisory 경고 | ADOPT (메커니즘 정밀화) | **R1** | "verifier가 opus로 돌았다"는 doc-verifier 신뢰모델의 전제인데 현재 미강제. OMC의 풀 tier-alias 머신은 불필요. 정밀화(AC-2): Claude Code는 agent 정의의 model을 Task 호출에 자동 적용하지 않으므로 **model 미지정이 기본 상태 = 정상**으로 취급하고, 감지 대상은 "명시적으로 잘못 지정된 model"로 한정 + 신뢰도가 더 높은 "옳은 subagent_type이 호출됐는가" 검사를 병행 검토. 전제 조건(완전성 비평 #2): `agents/doc-planner.md` frontmatter가 `model: opus` 고정이라 default(--direct) 경로까지 opus로 태움 — R1에서 sonnet으로 내리고 `--consensus`(Deliberate)만 opus 승격하도록 정합화해야 G4가 자기 저장소에서 오탐 없이 출발 |
| G5 | docs-pilot 스테이지별 delegation evidence 마커(`OMD stage <n> → spawned doc-<agent> | skipped: <reason>`) + Stop-guard가 누락 grep | ADOPT | R4 | G1의 Stop-guard 골격 위에 얹힘 → R1 이후 |
| G6 | ownership-marker 삭제 안전장치 — `.omd-authored` manifest, 목록 밖/해시 변경 파일은 AskUserQuestion 확인 | ADOPT | R4 | D4의 artifact-set manifest와 자연 통합(같은 manifest 파일) |
| G7 | **format-card 엔진 버전 고정** — 빌드 시 실측 엔진 버전(python-pptx.__version__, soffice --version)을 카드 `measured on` 스탬프와 비교, 불일치 시 VERIFIED → `UNVERIFIED (engine drift)` 강등 | ADOPT | **R1** | 신규 카드(mkdocs 등)가 생기기 **전에** 규칙을 확립해야 카드 2배 증가 후 소급 비용을 안 치름 |

### 3.2 omx 선례에서 추가 채택

| 항목 | 판정 | 릴리스 | 근거 |
|:---|:---|:---|:---|
| **버전 SSOT + sync 테스트** — plugin.json `version`이 SSOT, README 표기와 drift를 pytest가 잡음 | ADOPT | **R1** | omx `scripts/sync_version.py`+`test_version_sync.py` 선례. H3 직결 |
| **distribution-axiom 테스트** — 배포 파일 전체에서 개인 식별자·절대경로·머신 특정 값 금지어 스캔 | ADOPT (골격 명시) | **R1** | omx D12 선례. §1.2 원칙 1의 기계화. 구현 골격(DT-3): omx 실물 테스트의 FORBIDDEN 목록은 그 프로젝트 전용 하드코딩 토큰이므로 복사 금지 — ① 스캔 대상은 omd 실제 배포 트리(skills/*/SKILL.md, agents/*.md, hooks/*.py, references/**)로 재정의 ② 구현 세션의 개인 식별자를 금지어 목록 자체에 새겨넣지 말 것(그 자체가 위반) — 토큰 목록 vs 정규식 패턴(홈경로·이메일) 선택은 R1 plan에 위임 |
| skill-contract 테스트 — 스킬 본문이 참조하는 파일·카드·훅이 실제 존재하는지 검증 | ADOPT | R2 | omx `test_skills_reference_real_verbs.py` 선례(존재하지 않는 verb 참조 drift 실사고). omd판: 스킬이 가리키는 references/ 경로 실존 검사 — H7(themes 미연결) 재발 방지 |
| pipeline frontmatter(skills-authoring 16장) — 스킬 frontmatter로 handoff 계약 선언 | DEFER | R5+ | docs-pilot 본문 하드코딩으로 당장 동작. 구조 개선이지 보증 개선이 아님 |
| "Confirmed prior findings는 표로 압축, 재설명 금지" 문서 원칙 | ADOPT | 이 문서부터 | §3.1 표가 그 적용 |

**방법론 잠금**: omx의 교훈대로 REJECT/NA 판정은 서브시스템이 아니라 **sub-mechanism 단위**까지 내려가 재검증했다(예: "agents catalog는 이미 있음 → 전체 스킵"이 아니라 그 안의 model-tier 강제만 분리 채택 = G4).

### 3.3 Deliberately not adopting (기각 — 재검토 방지용 영구 기록)

- **MCP bridge / tool registry** — omd는 의도적으로 Node MCP 런타임 의존성 0 (python-pptx/docx 직접 구동). wiki_query는 abstract function으로 남겨 미래 교체점만 유지.
- **team/parallel workers** — 콘텐츠 안전 때문에 single-careful sequential이 omd 정체성 (docs-pilot Do_Not_Use_When 명시). 신규 텍스트 장르에도 동일 적용.
- **hard-block Stop hook (`decision:block`)** — freeze 실사고 이력으로 기각된 결정 유지. 모든 게이트는 advisory+fail-open.
- **ambiguity 정량화(가중합/threshold)** — 기존 판정("document work엔 근거 약함") 유지, 4차원 정성 게이트 존속.
- **embedding/vector 검색** — 영구 금지 (기존 불변식).
- **self-improve / ultragoal / autoresearch 루프** — 코드 최적화 도메인 전용. 단 ultragoal의 "definition of done을 검증된 JSON으로" 패턴은 doc-verifier Output_Format(Status/Blockers/integrity 표/snapshot)에 **부분** 반영 — 정정(심층 채굴 MQ-2 실물 대조): 현재는 기계 스키마 검증이 아닌 마크다운 표 수준이다. fenced JSON 블록으로의 격상 여부는 R2 plan에서 결정 — 찬성 근거(필드 완결성을 기계가 확인, 신규 카드에 처음부터 공통 적용)와 반대 근거(표와 이원화 시 SSOT 분열, docs-revise가 이미 표를 직접 소비)가 각각 독립 검증에서 확인돼 상반되므로 스펙 층에서 못박지 않는다.
- **HUD / 알림 / CLI 멀티모델(ask·ccg)** — 배치 문서 파이프라인과 무관, 패키징은 claudebase 책임 영역.
- **Antora** — 멀티 Git 저장소 문서 집계 오케스트레이터. omd의 "한 산출물 한 slug" 모델 밖 (§4.2 엔진 비교에서 기각).
- **semantic-release식 완전 자동 릴리스/발행** — "사용자 승인 없는 자동 발행 금지"는 omd판 도메인 불가침 규칙(omx의 "training launch never auto-fired" 대응). CHANGELOG는 keep-a-changelog 수동 저작+기계 검증으로 간다.
- **LLM 의미 린트(evaluateUsingLLM류)를 verify 게이트에 편입** — 그 역할은 이미 doc-inspector(형성적, opus)의 소관. verify(총괄)는 결정론적 체크만 담는다는 inspect/verify 분리 원칙 유지.

### 3.4 OMC 심층 채굴 추가 채택 (ultracode 2라운드 — 부록 B)

19챕터 전량을 8클러스터로 sub-mechanism 채굴 → 후보별 적대적 검증(기각 기본값) → opus 종합을 **2회 독립 실행**(1차 + rate-limit 유실 클러스터 보완 재실행이 사실상 재채굴이 됨)한 교차 확정분. 총 후보 52건 중 스켑틱 검증·교차 대조를 통과한 것만 채택 — 기각률 약 2/3.

| ID | 메커니즘 | 출처 | 릴리스 | effort | priority | 이식안 요약 |
|:--|:---|:---|:--|:--|:--|:---|
| AC-1a | **Test-enforced Final_Response_Contract** — 5개 에이전트 프롬프트의 필수 마커·자기승인 금지 정규식을 pytest로 정적 강제 (양 라운드 모두 확정) | 12-agents-catalog.md:106 | **R1** | S | high | `tests/test_agent_final_contract.py` 신설(stdlib frontmatter 파싱). 에이전트별 필수 마커(doc-verifier `### Verdict`·`PASS \| FAIL`, doc-planner 구조 프레임 헤더, doc-inspector `## Formative Review` 등) + 공통 금지 정규식(판정 없는 단독 승인 문구). 'never approve your own work' 존재 assert는 doc-verifier·doc-inspector 2종만 |
| IA-1 | **skill 컨텍스트 예산 회귀 테스트** (압축 shim 미도입 — 예산 가드만) | 16-skills-authoring.md §Progressive disclosure | **R1** | S | medium | `tests/test_skill_budget.py` — `skills/*/SKILL.md` 합계 상한 100KiB(omd 실측 58KiB에서 독립 도출 — OMC 64KiB는 압축 후 잣대라 유추 금지) assert. §4.4가 본문을 늘리기 **전에** 상한을 잠금(G7과 동형 논리). distribution-axiom 테스트와 동일 커밋 |
| HG-3 | **content-hash advisory 쿨다운** | 02-hooks.md:85, 19장:86 | **R1** | S | low | `.omd/.hook-throttle.json`(세션 전역 단일 파일 — docs_verify_emit.py는 file_path 문맥이 없어 slug 단위 불가)에 `{message_hash: ts}`, 리마인더 발화 전 sha256 대조 → 쿨다운(기본 10분, env override) 내 침묵, IO 실패 fail-open. G1 보강 ③(Stop-hook 문구 완화)과 훅이 달라 상보적 |
| PL-3 | **placeholder 잔존 스캔** — 미완성 산출물 차단 | 09-research.md:181-183 | **R2** | S | high | repo-docs verify gate에 ⑦로 편입(§4.3 반영 완료): `\[.*\]`·TODO·TBD·CHANGEME·`your-*-here` grep, 잔존 시 FAIL. doc-verifier가 grep 한 줄로 실행 |
| AC-1b | **빌린 엔진 stdout 강제 아티팩트 캡처** | 14-cli-interop.md:34-67 | **R2** | S | medium | doc-verifier가 mkdocs/markdownlint/lychee 실행 시 stdout+stderr를 `.omd/<slug>/verify-runs/<engine>-<ts>.log`로 성공·실패 무관 항상 저장, 리포트에는 경로만 링크. output-layout §2 서브디렉토리에 `verify-runs/` 추가 |
| PL-1 | **component-wise weakest-score aggregation** | 08-planning.md:70 | R2 (addendum) | S | medium | docs-intake 4차원 판정을 구성요소 단위로 실행하고 전체 판정은 컴포넌트별 최솟값 — "가장 흐린 컴포넌트가 게이트를 결정, 한 요소의 선명함이 형제의 흐림을 가리지 않는다" 한 줄. §4.4-8과 별개의 독립 문장 수정 |
| KN-2 | **CJK 바이그램 토크나이저** — wiki 검색 전처리 3단(Latin 어절 / CJK 1+2-gram / 기타 폴백) | 11-knowledge-lifecycle.md §Query | **R4** | S | high | `references/wiki/query_helper.py`(stdlib re/unicodedata, 훅 미등록 선택 유틸). **omd wiki README가 이미 "CJK bi-gram 포함 keyword matching"을 계약으로 명시했으나 구현 코드가 없는 계약-미이행 상태의 이행** — 신규 기능이 아니라 약속 이행. capture(R4)로 wiki에 실데이터가 쌓이는 릴리스와 동시 |
| KN-3 | **safeWikiPath 동형 경로 가드** — wiki 쓰기 직전 `/`·`\`·`..` 거부 + resolve-prefix 재확인 | wiki storage 분석 §safeWikiPath | R4 | S | medium | docs-learn/docs-pilot이 `.omd/wiki/**` Write 직전 호출하는 헬퍼(KN-2 유틸에 동봉). **해시 폴백 슬러그는 기각** — output-layout §1.2의 "사용자에게 ASCII 슬러그 확인" 기존 정책과 충돌하는 이중 해법 |
| ST-3 | **ascent walk $HOME 하한 명문화** | 15-lib-config-state.md §Anchor resolution | R4 | S | low | `references/wiki/README.md` ascent 서술에 "$HOME 도달 시 중단" 한 줄 — 얕은 트리에서 무관 프로젝트들이 우연한 상위 `.omd/`로 병합돼 기밀 격리 게이트가 뚫리는 사고 예방. (주의: "파일시스템 루트까지"는 OMC의 별개 메커니즘 하한이므로 혼동 인용 금지) |
| KN-4 | **wiki 파일명 영문 슬러그 규칙 명문화** | 11장:33·wiki storage §titleToSlug | R4 | S | low | README에 "주제가 한국어여도 파일명은 영문 키워드 의역" 한 줄(기존 관행의 명문화). `hashlib` 해시 폴백 코드는 **capture 훅이 실제 쓰기 코드를 갖는 시점**(R4 §4.5)에 그 코드 안에서만 — LLM 즉석 해시 지시는 결정론성 미보장이라 배제 |

**기존 잠긴 항목으로의 흡수분** (독립 행 없음 — R2/R4 plan 작성 시 해당 태스크의 acceptance/체크리스트에 한 줄로 편입):
- **G1-chk(HG-2)**: G1 Stop 훅 진입부에 `stop_hook_active===true`면 즉시 pass(리마인드 생략)하는 재진입 가드 — omd 최초의 Stop 훅이므로 이중-block 루프 방어를 처음부터 내장. G1 태스크 체크리스트 한 줄, 공수 0.
- **ST-1(atomic write)**: `manifest.json`·`.verify-pending`은 tmp파일(`.{name}.tmp.{uuid}`)에 먼저 쓰고 `os.replace()` 교체, 직접 open+truncate 금지 — §4.4-1(output-layout 개정)·§4.4-3(doc-verifier) acceptance에 한 줄. half-write된 manifest를 "파일 없음"으로 오판하면 G6 ownership 가드가 무력화되므로 **G6 신뢰성의 하부 전제**.
- **AC-4(죽은 상호참조 감지)**: §3.2 skill-contract 테스트의 스캔 대상을 `skills/*.md → references/`에서 `+ agents/*.md`로 한 줄 확장.
- **PR-1(ontology-stability 재수렴 신호)**: docs-intake challenge round마다 "구성요소 목록이 이전 라운드와 몇 개 겹치는가(재명명=겹침)"를 한 줄 기록 — §4.4-8(앞단 일반화)의 하위 스텝으로 흡수, 장르 조건부 분기 신설 금지(D1).

**교차 검증에서 기각·보류 확정** (재검토 방지 기록): PreCompact wiki 요약 배너(1차 확정 → 2차 재검증 기각 — omd wiki 참조는 에이전트 정의에 박힌 pre-commitment **pull** 계약이라 "compact 후 잊는" 실패모드 자체가 부재) / docs-revise 하드 상한 카운터(단일 세션 prompt 루프라 "세션 재시작으로 연장 사실 소실" 위협이 실재하지 않음 — Stop-hook 다세션 루프로 확장될 때만 조건부 재검토) / MCP 도구 injection hygiene(이식 대상 인프라가 omd에 없음 — wiki_query가 실제 MCP로 전환되는 시점의 R5+ 조건부) / 해시 폴백 슬러그·withWikiLock·evidence-tag grammar·세션 ownership envelope(각각 기존 정책 충돌·single-careful 불변식상 불필요·소비자 부재·경로 네임스페이스가 이미 격리).

---

## 4. 신규 포맷 확장 설계 (프로그램 주축)

### 4.1 잠금 결정 (Locked decisions)

| # | 결정 | 근거 |
|:--|:---|:---|
| D1 | **새 포맷 = 새 카드, 새 스킬 아님.** repo-docs·site는 기존 stage 파이프라인에 카드 추가로 편입 (stage-centric·format-as-variable 불변식 유지) | §2.3 |
| D2 | **site의 1차 엔진 = MkDocs + Material.** Docusaurus는 카드 내 "documented alternative"로만 기록(별도 카드 없음, R5+ 재검토) | §4.2 비교 — Python 의존성(기존 스택 동일 생태계), 단일 YAML 설정, 내장 `--strict` 기계 게이트. LLM 프로그래매틱 생성 친화도 최상 |
| D3 | **텍스트 장르 verify = 결정론적 exit-code 체인 + fresh-read.** 외부 린터(markdownlint-cli2, lychee, Vale)는 soffice와 같은 "빌린 엔진" — 카드가 머신별 VERIFIED 스탬프와 미설치 시 degrade 경로를 정의. **degrade의 verdict 규칙(완전성 비평 #6): 필수 엔진 미설치 시 PASS도 FAIL도 아닌 `UNVERIFIED (engine unavailable)` + 무엇을 검증 못 했는지 정직 표명** — hwpx 카드의 conditional render gate("렌더 못 하면 구조 검증기가 게이트가 되고 시각 정독 못 했다고 표명") 선례 계승, G7의 engine-drift 강등과 동형. 미설치를 조용한 PASS로 흘리면 verify 층에서 1위 실패모드를 재생산하고, FAIL로 막으면 D6 위반 — 둘 다 배제 | "엔진은 빌리고 두뇌는 만든다" 원칙의 텍스트판. 훅은 stdlib-only 유지 — 린터 실행은 훅이 아니라 doc-verifier의 Bash 경유 |
| D4 | **artifact-set 일반화**: 단일 파일 포맷은 기존 `outputs/<slug>/current.<ext>` 유지, 다중 파일 포맷은 `outputs/<slug>/current/` 디렉토리 + `.omd/<slug>/manifest.json`(경로+해시 목록). 불변식 재정의 — "사용자가 보는 진입점은 정확히 하나의 current 엔트리". 심층 감사 보강: ① 다중 파일의 버전 스냅샷은 `.omd/<slug>/versions/v{NN}_{date}_{summary}/` **디렉토리 통째 복사**로 확정 — output-layout.md §3/§5.2를 artifact-set 겸용으로 재작성(LC-1) ② manifest의 `role` 필드가 고정 상대경로 파일(CODEOWNERS, `.github/ISSUE_TEMPLATE/` 등)의 배치 정보를 담아, 사용자가 저장소로 복사할 때 상대 경로 보존을 카드가 안내(LC-2 — 자동 배치는 §8 원칙대로 하지 않음) | F1 해소. manifest는 G6 ownership 안전장치와 파일 공유 |
| D5 | **verify 트리거 이원화**: 오피스 계열=기존 Bash PostToolUse 유지, md 계열=Edit\|Write PostToolUse(oms .tex 모델) 신설. slug 판별 알고리즘(HK-3 — omd가 처음 설계, oms에 선례 없음): payload의 file_path에서 `outputs/`·`.omd/` 루트 직후 첫 path segment를 slug로 추출(stdlib os.path 기반). 단일 파일(`current.<ext>`)·artifact-set(`current/*`) 두 케이스에 더해 **site의 중첩 디렉토리 트리 픽스처까지 R2 단위 테스트에 선포함**(실물은 R3지만 경로 구조는 지금 검증 — 인프라가 가장 단순한 소비자로만 검증된 채 잠기는 것 방지, 완전성 비평 #5) | F2 해소. 훅 주석이 이미 이 방향을 가리킴 |
| D6 | **fail-open advisory 전면 유지** — 신규 게이트 전부 additionalContext 리마인드, `decision:block` 금지 | freeze 실사고 이력 |
| D7 | **FORM-only 학습 불변식의 텍스트 확장**: 학습 가능=README 섹션 순서 선호·voice·배지 스타일·changelog 그룹핑 컨벤션·nav 구조 패턴 / 영구 금지=프로젝트 사실·API 이름·수치·링크 대상 | anti-pattern F 확장. 텍스트 장르는 form과 content의 경계가 오피스보다 흐리므로 카드에 경계 예시를 명시 |
| D8 | **distribution axiom 기계화**: 배포 파일에서 개인 식별자·절대경로 금지를 pytest 금지어 스캔으로 강제 | §1.2 원칙 1, omx D12 선례, claudebase 대원칙과 동형 |

### 4.2 site 포맷 카드 — `references/formats/site.md`

**엔진 선정 근거** (§9 facet 1 조사 요약):

| 엔진 | 의존성 | 설정 | 내장 기계 게이트 | 판정 |
|:---|:---|:---|:---|:---|
| **MkDocs+Material** | Python | 단일 YAML | `mkdocs build --strict` + `validation:`(nav/links/anchors 개별 제어) | **1차 엔진** — 기존 Python 스택과 동일 생태계, LLM 생성 친화도 최상 |
| Docusaurus | Node | JS 코드 | `onBrokenLinks: 'throw'` 기본값 | documented alternative (React 생태계 사용자용, R5+) |
| Sphinx | Python | Python(conf.py) | `-W`/`-n`/linkcheck | 기각 — API autodoc이 핵심인데 omd는 코드 문서 생성기가 아님. reST 학습 비용 |
| VitePress / Starlight | Node | TS/JS | 불명확/옵트인 플러그인 | 기각 — Vue 종속 / strict가 내장 아님 |
| Antora | Node | YAML playbook | 없음 | 기각 — 멀티레포 오케스트레이션 전제 (§3.3) |

**카드가 담을 내용** — 카드 스키마 정정(FV-1): 실물 5개 카드는 고정 "8단"이 아니라 섹션 구성이 포맷별 가변이다. 공통 계약은 **필수 3섹션**(Engine 표 · Hard traps · Version-snapshot policy — 5/5 카드 공통) + 조건 섹션(License_Note는 anthropics/skills 출처 표기 시) + 포맷 고유 섹션 자유. 신규 카드도 이 "필수 3 + 가변" 계약을 따른다:

- Engine 표: `mkdocs` + `mkdocs-material`(빌드), `markdownlint-cli2`(문법), `lychee`(외부 링크, 선택적), Python 3.x. 각 행에 VERIFIED 여부 — **초기 카드는 전 항목 UNVERIFIED로 시작하고, R3의 실측 검증 태스크가 이 머신에서 스탬프를 찍는다** (pptx 카드가 함정을 실측으로 채운 것과 동일 절차).
- Hard traps 후보(조사 기반, 실측으로 승격 예정): strict 모드가 잡는 것/못 잡는 것 경계, `nav:` 누락 파일의 조용한 제외, mkdocs-material 버전 간 설정 키 drift, 한글 검색(CJK) 플러그인 요구사항.
- 포맷 고유 섹션: **Diátaxis 4분면**(tutorial/how-to/reference/explanation)을 nav 구조 설계의 기본 프레임으로 — docs-plan(doc-planner)이 site 포맷일 때 이 섹션을 읽고 아웃라인을 4분면에 매핑.
- verify gate 정의: ① `mkdocs build --strict` exit 0 ② markdownlint 통과 ③ 내부 링크·앵커 유효(strict validation) ④ 빌드된 HTML 대표 페이지 fresh-read(렌더 정독의 텍스트판) ⑤ nav 완결성(소스 md 전수가 nav에 등재 — 조용한 제외 함정 방지, --strict가 커버하는지 실측 확인 후 중복 제거). 이 "기계적 게이트 우선 + 렌더는 보조/불가 시 정직 표명" 원칙은 xlsx 카드(:52-56 구조 어서션이 1차 게이트)·hwpx 카드(:101-104 conditional render gate) 선례의 텍스트 장르 연장이며, 엔진 미설치 시 verdict는 D3의 `UNVERIFIED (engine unavailable)` 규칙을 따른다.
- no-reference 폴백: themes/ 오피스 팔레트가 아니라 mkdocs-material `palette:` 스키마(primary/accent + scheme)가 폴백 형식 (완전성 비평 #3).

**루브릭**: `references/rubrics/site-rubric.md` 신설 — PPTEval 3축 대신 (a) 빌드/링크 무결성(기계), (b) 정보 구조(Diátaxis 커버리지·nav 깊이·two-click 도달성), (c) 산문 품질(스타일 가이드 준수 — Vale 선택적). 근거는 §9 facet 3. doc-inspect 렌즈 구성은 3-lens 고정이 아니라 verify가 담당하지 않는 정성 축만큼 동적 결정 — site는 (a)가 verify 소관이므로 실질 2렌즈(정보 구조·산문) (PS-3).

### 4.3 repo-docs 포맷 카드 — `references/formats/repo-docs.md`

**다루는 산출물**: README.md(standard-readme spec), CHANGELOG.md(keep-a-changelog 1.1.0), CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/SUPPORT, 이슈/PR 템플릿, CODEOWNERS — "GitHub 저장소 문서 세트"라는 **장르 카드**(엔진 카드가 아님. 엔진은 순수 마크다운 + 린터 체인).

**카드가 담을 표준 지식** (§9 facet 2 조사 기반 — 카드에 URL 출처 명기):

- README: standard-readme 필수 섹션 순서(Title→Short Description(≤120자)→ToC(100줄↑ 필수)→Install→Usage→Contributing→License(항상 마지막)), 선택 섹션(Badges/Background/Security/Maintainers). Google README 가이드와의 수렴점.
- CHANGELOG: keep-a-changelog 7원칙, 6개 변경 유형(Added/Changed/Deprecated/Removed/Fixed/Security) 고정, `[Unreleased]` 최상단, ISO 8601 날짜, YANKED 표기.
- Community health files: root/`.github`/`docs` 3위치 탐색 규칙 + 조직 `.github` 저장소 폴백(public 필수, LICENSE는 폴백 불가), 이슈 템플릿은 `.github/ISSUE_TEMPLATE/` 고정 경로 + frontmatter 필수 필드.
- **CODEOWNERS hard traps**: 마지막 매치 우선(구체 규칙을 파일 하단에), 같은 패턴 다중 오너는 반드시 한 줄, 문법 오류 줄은 **조용히 스킵**(에러 없음 — 검증 스크립트가 잡아야 함), 경로 대소문자 구분.
- verify gate 정의: ① 필수 섹션 존재+순서(장르별 프리셋 — 라이브러리/CLI/데이터셋) ② 링크 유효성 ③ markdownlint ④ 코드블록 언어 태그 전수 ⑤ CHANGELOG 날짜 ISO 형식+버전 역순 ⑥ 배지 URL 형식 ⑦ placeholder 잔존 스캔(`\[.*\]`·TODO·TBD·CHANGEME·`your-*-here` grep — 미완성 산출물 차단, §3.4 PL-3). 이 6개 체크의 1차 근거는 standard-readme·keep-a-changelog·GitHub 공식 문서(전부 검증된 표준)이며, "기계 게이트 vs 수리 대상" 계층 구분의 참고 프레임으로 CHI 2026 README 린팅 논문의 "linting ladder"(checkable→customizable→blameable→fixable)를 인용한다 — **단 이 논문은 미검증 단일 출처(arXiv 2603.00331, 세션이 원문 실물 미확인)이므로 설계를 이 논문 용어에 못박지 않는다. R2 plan 착수 전 원문 검증 태스크 필수(§7 리스크 ④)**.

**루브릭**: `references/rubrics/repo-docs-rubric.md` — 기계 검증 가능 축(정확성·일관성·접근성 기초 등)은 verify로, 정성 축(환영하는 서두인가 등)은 doc-inspector 렌즈로 분배. CHI 2026의 7축 분류는 검증 후 채택 여부를 정할 **참고 예시**로만 기록(위와 동일 사유).

**템플릿 씨앗**: The Good Docs Project 템플릿 팩(오픈소스, Markdown)을 docs-standardize의 "양식 없음 시 기본 양식" 소스로 카드에 포인터 기록 — 단 코드/문구 복사가 아니라 구조 참조(License_Note 관례 준수).

**장르 운영 규정** (심층 감사 반영 — 카드 본문에 명문화할 것):
- **intake 세트 스코프 게이트**(완전성 비평 #4): repo-docs는 한 요청에 6~8종 파일을 동시 산출하는 세트 장르이므로, Gate 0에서 format·kind에 앞서 **산출물 세트 스코프**(전체 / README만 / 커뮤니티 헬스만)를 먼저 확정 — 선택 결과는 D4 manifest의 `role` 필드가 담는다.
- **doc-analyzer 입력 경계**(AC-3): 코드베이스 전체 정독 금지 — 입력을 기존 README·CHANGELOG·커뮤니티 헬스 파일 + package manifest(package.json 등)·CI 설정 + Grep/Glob 구조 스캔(파일 내용 전체 Read 아님) + 최근 커밋 로그 요약으로 **화이트리스트 한정** (스코프를 좁힌 기존 선례 있음 — readme 생성 도구들의 "manifest·lock·CI·구조" 수준).
- **산출물 배치**(LC-2): 산출물은 `outputs/<slug>/current/`에 머무른다 — README가 의미를 갖는 곳은 저장소 루트지만, 루트/`.github/`로의 배치는 §8 원칙("산출까지가 omd 소관, 발행은 사용자")대로 사용자 책임. 카드는 `cp -r` 안내와 상대 경로 보존 규칙만 제공, 자동 이동 없음.
- **no-reference 폴백**(완전성 비평 #3): themes/ 오피스 팔레트를 쓰지 않음 — 폴백은 장르 프리셋(라이브러리/CLI/데이터셋) 중 섹션 구성 선택.
- **엔진 미설치 degrade**: D3의 `UNVERIFIED (engine unavailable)` 규칙 적용 (xlsx·hwpx 카드의 구조-게이트-우선·정직-표명 선례 연장).

### 4.4 공통 인프라 일반화 (R2에서 수행 — repo-docs가 첫 소비자, 심층 감사로 6→13항 확장)

관통 원칙: 스킬/에이전트 본문의 오피스 하드코딩("≥150dpi", "zip CRC 5-check", "narrative arc")을 전부 **"카드가 정의한다"로 위임**하는 동일 패턴이다. 포맷별 if/else를 본문에 심는 방식은 D1 위반이라 채택하지 않는다.

1. `references/output-layout.md` 개정: D4 artifact-set 불변식 + manifest.json 스키마(`{paths: [{path, sha256, role}], format, slug}`) + **§3/§5.2 버전 스냅샷 절을 artifact-set 겸용으로 재작성**(다중 파일=versions/ 디렉토리 통째 복사, LC-1).
2. `hooks/docs_verify_emit.py`: md 계열 Edit|Write 트리거 추가(D5) + slug 판별 알고리즘 전용 태스크(단위 테스트 포함 — site 중첩 트리 픽스처 선포함, HK-3), DOC_EXTS 죽은 상수 정리(H4는 R1에서 선처리), BUILD_SIGNALS에 `mkdocs build` 추가는 R3.
3. `agents/doc-verifier.md`: integrity check를 "카드가 정의한 verify gate를 실행한다"로 일반화 — zip CRC 5-check는 OOXML 카드 소관으로 이동(F3) + **snapshot-correlation 토큰을 D4 manifest와 연동** — 다중 파일은 manifest 내 `{path, sha256}` 목록의 결합 해시를 스냅샷 식별자로(AC-5).
4. `agents/doc-builder.md`: "Write the build script(python-pptx…)·PNG 렌더 sanity check·shape assertion" 오피스 전용 절차 서술을 "카드가 정의한 엔진 구동 방식(빌드 스크립트+실행 또는 md 직접 Write)과 sanity check(PNG 렌더 또는 mkdocs build 후 HTML fresh-read)"로 일반화 — doc-verifier.md:46이 이 둘을 self-gate/독립재검증 쌍으로 명시하므로 **항목 3과 동일 커밋**에서 처리해 쌍이 깨지지 않게(AC-4·PS-5). 세부 분기 방식은 R2 plan 태스크 층위로 위임.
5. `skills/docs-inspect/SKILL.md`·`skills/docs-verify/SKILL.md`: `<Checks>`·`<Steps>` 절의 "renders all slides at ≥150dpi"·구체 5-check 나열을 "카드가 정의한 verify gate 실행"으로 재작성, `<Gate>`의 "Integrity 5/5"는 "카드 정의 gate 전항목 통과"로 일반화 — **항목 3·4와 동일 커밋 단위**(지시-실행 불일치 방지, PS-1). docs-inspect의 Lens 1/2/3 하드코딩은 포맷별 루브릭 카드 참조·동적 렌즈 결정으로(PS-3).
6. `skills/docs-standardize/SKILL.md`: Mandatory_When의 pptx 전제 문구를 포맷 조건부로, Gate/Steps의 "PNG round-trip ≥85%"를 분기 — 렌더 가능 포맷은 유지, 텍스트 장르는 카드가 정의한 표준 컨벤션(섹션 순서·voice·배지) checklist 일치 확인으로 대체(F6/PS-2 — 새 계량 메커니즘 발명 없이 D3 프레임 재사용).
7. `skills/docs-revise/SKILL.md`: Execution_Policy의 acceptance criteria 4항 중 하드코딩된 "Integrity 5/5"·"Full PNG read-through"를 "pass 정의는 doc-verifier가 대상 카드의 verify gate 판정을 그대로 따른다"로 재작성 — 항목 3과 자동 동기화(PS-4). recur-방지 항목은 포맷 불가지론적이므로 유지.
8. **파이프라인 앞단 일반화**(F7 — 이것 없이는 신규 장르가 진입 자체를 못 함): `skills/docs-intake/SKILL.md`·`skills/docs-plan/SKILL.md`·`agents/doc-planner.md`·`agents/doc-analyzer.md`의 발표 전용 어휘("slides"·"narrative arc"·"tone preset (defense/conference/lecture)")를 "카드가 장르별 intake 질문·구조 프레임을 정의"로 일반화 — doc-planner Success_Criteria의 'narrative arc'는 '카드가 정의한 구조 프레임(오피스=arc, repo-docs=섹션 프리셋, site=Diátaxis 4분면)'으로 재서술 (완전성 비평 #1).
9. `hooks/route_emit.py` CHECKPOINT 본문 개정: 포맷 열거 **2곳**(FORMAT 슬롯 :24 + STAGE 토큰 줄 :40)에 `repo-docs|site` 추가(pdf는 H5 층위 결정에 따름) + 본문 문자열을 assert하는 **route_emit 테스트 전반** 재검증 — CHECKPOINT 텍스트 회귀를 R2/R3 plan의 독립 태스크로 명시 (F5).
10. `skills/docs-build/SKILL.md` Format_Knowledge 표에 신규 카드 행 추가.
11. `references/learning-protocol.md`: D7 경계 예시(텍스트 장르의 form vs content) 추가.
12. `skills/docs-convert/SKILL.md`·`skills/docs-translate/SKILL.md`: artifact-set(다중 파일 `current/`) 입력을 받으면 **명시적 미지원 응답 후 정지**하는 최소 가드 한 줄 — R5+ 확장 이연이 침묵이 아니라 의도된 제한임을 표시, 반쪽 번역 산출 실패모드 예방(LC-3).
13. `references/themes/README.md`: "오피스 포맷 전용 — 텍스트 장르의 no-reference 폴백은 카드가 정의" 명시(F8).

### 4.5 wiki 특화 루프의 확장 (R4)

OMC 지식 수명주기 분석(§9 ①)의 핵심 패턴 — **capture(값싸고 자동, 3초 예산)와 curate(LLM 판단, 사람 게이트)의 구조적 분리** — 를 omd에 완성한다. 현재 omd는 curate 쪽(learned.md 승격 게이트)만 있고 **capture 메커니즘이 부재해 원장이 채워질 경로 자체가 없다** (빈 원장은 설계상 정상 초기 상태다 — 문제는 "비어 있음"이 아니라 "채워질 수 없음"이다. `.omd/learned.md:14` "Empty ledger = correct initial state" 참조). R4에서: (a) wiki lint(G3)로 건강 체크, (b) notepad pruning(G2)으로 작업 메모리 위생, (c) 세션 관찰의 저비용 자동 append(OBS 초안 생성 — 승격은 여전히 사람 게이트) 도입. 이것이 "사용자에게 점점 특화"가 실제로 작동하게 만드는 마지막 조각이며, §0의 경쟁 갭 (b)를 지키는 축이다.

---

## 5. Release train

| 릴리스 | 버전 | 이름 | 스코프 요약 | 규모 추정 |
|:---|:---|:---|:---|:---|
| **R1** | v0.1.0 | 위생 + 핵심 게이트 | H1–H4·H6·H7 수리 + H5 층위 결정, 버전 SSOT 확립 + **omd 자신의 CHANGELOG 정책 결정**(현행 commit-SHA versioning(CHANGELOG.md:5 명시 정책) → keep-a-changelog+semver 전환 여부 — 정책 변경이므로 사용자 승인 항목), distribution-axiom 테스트, G1(Stop-guard)·G4(model 가드)·G7(엔진 버전 고정), **5개 에이전트 frontmatter model 정합 감사**(doc-planner `model: opus`→sonnet 하향, `--consensus`/Deliberate만 opus 승격 — G4가 자기 저장소에서 오탐 없이 출발하기 위한 전제, 완전성 비평 #2), 심층 채굴 3건(§3.4 — AC-1a Final_Response_Contract pytest·IA-1 skill 예산 상한 테스트·HG-3 advisory 쿨다운, 전부 S) + G1 체크리스트에 stop_hook_active 재진입 가드 | 태스크 ~16 (G1/G4/G7이 각각 훅+센티널/가드+테스트로 2–3태스크) |
| **R2** | v0.2.0 | repo-docs 장르 | repo-docs 카드+루브릭, 공통 인프라 일반화(§4.4), skill-contract 테스트, CHI 논문 원문 검증(§7 리스크 ④), **dogfooding acceptance: omd 자신의 stale README/CHANGELOG(H6에서 1차 수리)를 신규 파이프라인으로 재생성 — PASS 기준은 repo-docs verify gate 통과(필수 섹션+순서, markdownlint, 내부 링크, ISO 날짜)** | 태스크 ~16+α (§4.4가 13항으로 확장 — 특히 앞단 일반화 #8·뒷단 일반화 쌍 #3-#7이 추가. §3.4의 PL-3·AC-1b·PL-1은 독립 소항목, ST-1·AC-4·PR-1·MQ-2 결정은 기존 태스크 acceptance에 한 줄 흡수라 순증 최소) |
| **R3** | v0.3.0 | site 장르 | site 카드+루브릭, mkdocs 엔진 실측 검증(카드 UNVERIFIED→VERIFIED 스탬프), Diátaxis plan 지식, E2E 파일럿(omd 자체 문서 사이트) | 태스크 ~10 |
| **R4** | v0.4.0 | 지식 수명주기 | G2(notepad)·G3(wiki lint)·G5(stage evidence)·G6(ownership manifest), capture 자동화, 심층 채굴 wiki 계열 4건(§3.4 — KN-2 CJK bi-gram 토크나이저(README 계약 이행)·KN-3 safeWikiPath 경로 가드·ST-3 ascent $HOME 하한·KN-4 영문 슬러그 규칙, 전부 S) | 태스크 ~12 |
| R5+ | — | deferred | Docusaurus 대안 카드, pipeline frontmatter, docs-translate/convert의 md 확장, hwpx/pdf 미검증 항목 검증 스윕, pptx editing 기법 실검증, Vale 스타일 패키지 심화, The Good Docs 팩 통합 확대 | 백로그 |

**순서 근거** (omx의 hybrid ordering 원칙): 깨진 테스트 위에 새 기능을 쌓지 않는다(R1 선행 절대). repo-docs를 site보다 먼저 두는 이유 — ① 새 엔진 설치가 0(순수 마크다운)이라 인프라 일반화(§4.4)를 최소 블라스트 반경으로 검증, ② 사용자 가치 밀도 최고(모든 저장소가 README를 가짐), ③ site는 R2가 만든 artifact-set·Edit|Write 트리거를 그대로 소비하므로 의존 방향이 자연스러움. R4를 마지막에 두는 이유 — 특화 루프는 신규 장르가 실제로 돌아야 학습 관찰이 쌓이기 시작하므로.

**R1 build-order constraints**: H1·H2(테스트 green) → H3(버전 SSOT — CHANGELOG 정책 결정 선행) → 나머지 위생(H4·H6·H7 수리, H5 층위 결정) → 신규 테스트(distribution-axiom, version-sync) → 신규 게이트(G7 → G1 → G4; G7이 먼저인 이유는 카드 규칙 확립이 이후 모든 카드 작업의 전제라서).

**R2 build-order constraints**: output-layout 개정(D4, 버전 스냅샷 규칙 포함) → verify 훅 트리거(D5 — slug 판별 단위 테스트에 site 중첩 트리 픽스처 선포함) → **뒷단 일반화 묶음**(§4.4의 3·4·5·6·7 — doc-verifier·doc-builder·inspect/verify/revise/standardize의 카드 위임 전환, 쌍 보존을 위해 인접 커밋 단위) → repo-docs 카드+루브릭 → **앞단 일반화**(§4.4-8 — 카드가 정의한 장르별 intake 질문·구조 프레임을 소비하므로 카드 이후) → route/tests(§4.4-9) → dogfooding acceptance. 카드가 인프라보다 먼저 오면 카드가 정의한 verify gate를 실행할 곳이 없고, 앞단 일반화가 카드보다 먼저 오면 참조할 장르 프레임이 없다.

---

## 6. Program mechanics (omx recipe 승계, 릴리스 간 재설계 금지)

각 릴리스는 동일 사이클을 반복한다: 이 문서(§5 스코프)를 입력으로 **superpowers:writing-plans**가 릴리스별 TDD plan(`docs/superpowers/plans/YYYY-MM-DD-omd-vX.Y.Z-rN.md`) 작성 → critic(opus) 독립 검토 → **사용자 승인 게이트** → 전용 브랜치(`feat/v0.1.0-r1` 등) → **superpowers:subagent-driven-development**(implementer/reviewer=sonnet, 2회 반려 시 opus 승격) → 마지막 태스크는 항상 Release(버전 bump+CHANGELOG+README+전체 테스트, LOCAL ONLY) → whole-branch 리뷰(opus) → 사용자 merge 게이트(`--no-ff`).

버전 SSOT: `.claude-plugin/plugin.json`의 `version` 필드(R1에서 신설). 정정(DT-1·DT-2): omx 실물 `sync_version.py`의 fan-out 대상은 `pyproject.toml`인데 omd에는 없고(순수 플러그인), omx 정책은 "버전 마커는 **이미 있는 곳만** 갱신하고 신설 주입하지 않는다"이며 현재 omd README에는 버전 마커가 전혀 없다. 따라서 R1의 `test_version_sync.py`는 plugin.json 단독 검사(version 필드 존재 + 유효한 semver 형식)로 시작하고 README는 fan-out 대상에서 제외 — README 버전 배지 신설 여부는 R2 dogfooding(README 재생성) 범위에서 별도 판단. 커밋 컨벤션은 기존 이력(`feat(omd):`/`[docs]`) 유지.

---

## 7. Cross-cutting

- **에러 철학**: 모든 신규 훅은 fail-open(예외 시 조용히 통과) + advisory. 보증이 필요한 검사는 훅이 아니라 pytest/verify gate에 이중화 — "hook은 유일한 guarantee 운반체가 될 수 없다"(omx D9 승계).
- **테스트 전략**: 기존 4개 계약 테스트 체계 유지·확장. 신규 테스트는 전부 회귀 가드형(훅 출력·plugin.json drift·금지어 스캔·버전 sync·스킬 참조 실존). 에이전트 동작 통합 테스트 공백(전수조사 F절)은 dogfooding acceptance(R2·R3의 E2E 파일럿)로 부분 대체 — 완전한 통합 테스트 하네스는 R5+ 백로그.
- **배포 경계**: 훅·스크립트=stdlib-only Python. 외부 린터·빌더=카드가 관리하는 "빌린 엔진"(머신별 설치, VERIFIED 스탬프, degrade 경로 필수). 이 경계 덕에 플러그인 자체는 의존성 0으로 배포 가능.
- **하위 호환**: 기존 4개 오피스 포맷의 파이프라인·카드·verify 경로는 무변경(R1 위생 수리 제외). output-layout 개정도 단일 파일 포맷의 기존 경로를 보존(D4).
- **리스크**: ① mkdocs 함정 실측에서 예상 밖 규모 발견 시 R3 스코프 초과 — 카드 UNVERIFIED 상태로도 R3 출하 가능하게 acceptance를 "E2E 파일럿 1회 성공"으로 한정. ② md 계열 Edit|Write 트리거의 발화 빈도 과다(모든 md 편집에 리마인더) — slug 컨텍스트(`.omd/<slug>/` 존재) 있는 경우로 발화 조건을 좁혀 노이즈 억제. ③ repo-docs verify의 외부 링크 체크는 네트워크 의존 — 기본 게이트에서 제외하고 내부 앵커만 필수, 외부 링크는 lychee 설치 시 선택 게이트(D3 degrade 경로). ④ **CHI 2026 README 린팅 논문(arXiv 2603.00331)은 원문 미확인 단일 출처** — linting ladder·7축 인용의 진위를 R2 plan 착수 전 원문으로 검증하고, 검증 실패 시 해당 참조를 제거해도 verify gate 설계(1차 근거는 검증된 표준들)가 성립하도록 §4.3에 이미 완충되어 있음. ⑤ **marketplace 캐시 함정**(DT-4): `plugin.json` 버전 bump 후 `/plugin marketplace update`는 디스크 캐시만 갱신하며 현재 세션은 `/clear`·`/compact`로 반영되지 않음 — release 사이클을 수행한 세션이 이어서 새 버전 스킬/훅을 검증하려면 Claude Code 앱 완전 재시작 필요(디스크 캐시 갱신≠프로세스 메모리 갱신). dogfooding acceptance나 릴리스 직후 자체 검증 시 유의. ⑥ **alert fatigue**(HK-2): 사용자가 verify를 의도적으로 미룬 경우 매 Stop마다 리마인드가 반복되는 피로 위험 — 완화는 훅 로직 변경이 아니라 advisory 문구 자체가 이를 흡수하도록 설계(G1 보강 ③)로 한정.

---

## 8. Out of scope (이 프로그램에서 하지 않는 것)

§3.3 기각 목록 전체 + 다음: 문서 **호스팅/배포**(GitHub Pages 발행 등 — 산출까지가 omd 소관, 발행은 사용자), 코드베이스 자동 분석 기반 API 레퍼런스 생성(Sphinx autodoc류 — omd는 코드 문서 생성기가 아니라 문서 저작 하네스), 다국어 사이트(i18n), AGENTS.md/CLAUDE.md 생성(OMC deepinit 소관), 실시간 협업 편집.

---

## 9. 근거 자료

**내부 문서**: ① claudebase OMC 심층분석 `~/claudebase/docs/reference/omc-deep-analysis-v4.15.2/`(INDEX, 01–19, gaps/oh-my-docs.md, gaps/oh-my-experiments.md) + `omc-wiki-skill-analysis.md` ② omx 선례 `~/oh-my-experiments/docs/2026-07-05-omc-v4.15.2-alignment-audit.md`, `docs/superpowers/specs/2026-07-05-omx-v0.2-program-design.md` 외 r2/r3 spec·plan, `docs/cross-harness-backport-decision.md` ③ omd 저장소 전수조사(2026-07-11 pytest 실측 포함).

**외부 조사** (document-specialist 4-facet, 2026-07-11):
- SSG: [MkDocs configuration](https://www.mkdocs.org/user-guide/configuration/) · [Material for MkDocs — Alternatives](https://squidfunk.github.io/mkdocs-material/alternatives/) · [Docusaurus config](https://docusaurus.io/docs/api/docusaurus-config) · [sphinx-build](https://www.sphinx-doc.org/en/master/man/sphinx-build.html) · [VitePress](https://vitepress.dev/guide/what-is-vitepress) · [Starlight](https://github.com/withastro/starlight) · [starlight-links-validator](https://github.com/HiDeoo/starlight-links-validator) · [Antora](https://docs.antora.org/antora/latest/)
- repo-docs 표준: [standard-readme spec](https://github.com/RichardLitt/standard-readme/blob/main/spec.md) · [Google README guide](https://google.github.io/styleguide/docguide/READMEs.html) · [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) · [GitHub community health files](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file) · [이슈/PR 템플릿](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates) · [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) · [CHI 2026 README 린팅 논문](https://arxiv.org/html/2603.00331)
- 품질 프레임워크: [Diátaxis](https://diataxis.fr/) · [Google developer documentation style guide](https://developers.google.com/style/) · [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice) · [Vale](https://vale.sh/) · [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) · [lychee](https://github.com/lycheeverse/lychee) · [The Good Docs Project](https://www.thegooddocsproject.dev/)
- AI 문서도구: [Mintlify AI-native](https://www.mintlify.com/docs/ai-native) · [GitBook AI](https://www.gitbook.com/features/ai) · [readme-ai](https://github.com/eli64s/readme-ai) · [Swimm](https://swimm.io/) · [Cursor hallucination limitations](https://cursor.com/learn/hallucination-limitations)

---

## 부록 A — ultracode 심층 감사 반영 대장 (2026-07-11)

6클러스터 감사관(33 에이전트) → 발견별 적대적 검증(기각 기본값) → opus 완전성 비평. 발견 26건 중 **확정 22 / 기각 4**, 비평 6건 추가. 전 항목의 반영 위치:

| ID | 심각도 | 요지 (한 줄) | 반영 위치 |
|:--|:--|:---|:---|
| PS-1 | major | docs-inspect·verify SKILL.md의 "≥150dpi"·5-check 하드코딩 — 뒷단 에이전트만 일반화하면 지시-실행 불일치 | §4.4-5 |
| PS-2 | major | docs-standardize의 PNG round-trip ≥85% 게이트가 텍스트 장르에서 불성립 | §2.2 F6, §4.4-6 |
| PS-3 | minor | inspect 3-lens(PPTEval 축) 하드코딩 — 장르별 동적 렌즈 필요 | §4.2 루브릭, §4.4-5 |
| PS-4 | minor | docs-revise acceptance 4항의 "Integrity 5/5" 하드코딩 | §4.4-7 |
| PS-5 | minor | doc-builder 절차 서술(빌드 스크립트·PNG 렌더)의 오피스 전제 | §4.4-4 |
| AC-2 | major | G4의 전제 오류 — Task 호출에 model 미지정이 기본 상태(불일치가 아니라 미지정) | §3.1 G4 |
| AC-3 | minor | doc-analyzer 입력 경계 부재 — repo-docs에서 코드베이스 전체로 스코프 폭발 위험 | §4.3 장르 운영 규정 |
| AC-4 | major | doc-builder 계약 전체가 오피스 바이너리 전제 — verifier와 쌍으로 일반화 필요 | §4.4-4 |
| AC-5 | minor | snapshot-correlation 토큰이 단일 파일 mtime/CRC 전제 — artifact-set과 불합치 | §4.4-3 |
| HK-1 | major | G1 센티널의 다중 slug 시나리오 미정의 — 세션 상태 없이 glob 전수 스캔으로 해소 | §3.1 G1 ① |
| HK-2 | major | 의도적 verify 유예 시 반복 리마인드 — advisory 문구로 흡수, 의도 파싱은 배제 | §3.1 G1 ③, §7 ⑥ |
| HK-3 | major | D5 slug 판별 메커니즘 완전 미정의 — file_path 첫 segment 추출로 확정, omd 최초 설계 | D5, §4.4-2 |
| HK-4 | minor | stale 센티널 — mtime으로 세션 이월분 구분 표시, TTL 자동 만료는 비채택 | §3.1 G1 ② |
| FV-1 | major | "카드 8단 스키마" 서술이 실물과 불일치 — 필수 3섹션+가변으로 정정 | §4.2 |
| FV-5 | minor | xlsx·hwpx의 "구조 게이트 우선·정직 표명" 선례를 텍스트 verify가 계승함을 명시 | §4.2, §4.3, D3 |
| LC-1 | major | artifact-set의 버전 스냅샷 방식 침묵 — versions/ 디렉토리 통째 복사로 확정 | D4, §4.4-1 |
| LC-2 | major | repo-docs 산출물은 저장소 루트에 있어야 의미 — output-layout 불변식과의 긴장을 §8 원칙+manifest role로 해소 | D4, §4.3 |
| LC-3 | minor | convert/translate가 artifact-set을 만나면 반쪽 산출 위험 — 명시적 미지원 가드 | §4.4-12 |
| DT-1 | major | version-sync의 omx fan-out 대상(pyproject)이 omd에 없음 — plugin.json 단독 검사로 축소 | §6 |
| DT-2 | minor | "README 배지 drift를 잡는다" 서술이 사실과 어긋남(마커 자체가 없음) | §6 |
| DT-3 | minor | distribution-axiom의 스캔 대상·금지어 목록 골격 미정의 | §3.2 |
| DT-4 | minor | marketplace 캐시는 앱 재시작 전 미반영 — 릴리스 직후 자체 검증 함정 | §7 ⑤ |
| 비평#1 | major | **파이프라인 앞단 4파일(intake·plan·planner·analyzer)의 발표 장르 하드코딩 — 신규 장르가 진입 자체를 못 함** | §2.2 F7, §4.4-8 |
| 비평#2 | major | doc-planner frontmatter `model: opus` 고정 — G4와 자기모순 + model_routing 정책 위반 | §3.1 G4, §5 R1 |
| 비평#3 | major | themes/ 폴백이 오피스 팔레트 전용 — 텍스트 장르에서 장르 불일치 폴백 | §2.2 F8, §4.2, §4.3, §4.4-13 |
| 비평#4 | minor | repo-docs는 세트 장르 — intake Gate 0에 산출물 세트 스코프 게이트 필요 | §4.3 장르 운영 규정 |
| 비평#5 | minor | D4/D5 인프라가 가장 단순한 소비자(repo-docs)로만 검증된 채 잠김 — site 중첩 트리 픽스처 선포함 | D5, §5 R2 build-order |
| 비평#6 | minor | 엔진 미설치 시 조용한 PASS/경직 FAIL 둘 다 불가 — `UNVERIFIED (engine unavailable)` verdict 신설 | D3, §4.2, §4.3 |

기각 4건(재검토 방지): 감사 발견 중 ① 설계 문서가 이미 다루는 내용의 재탕 ② 증거 파일:줄 불일치 ③ 불변식 충돌 제안이 스켑틱 검증에서 탈락 — 세부는 워크플로 저널 참조.

---

## 부록 B — OMC 심층 채굴 대장 (ultracode 2라운드, 2026-07-11)

방법: OMC deep-analysis 19챕터를 8클러스터(install-authoring / hooks-gate / state-lib / modes-quality / planning-research / knowledge / agents-catalog / na-mining)로 나눠 sub-mechanism 단위 채굴관(sonnet) → 후보별 적대적 검증관(sonnet, 기각 기본값·출처 실물 대조·불변식 5종 체크) → opus 종합. 1라운드(후보 27 → 확정 9 / 기각 18)에서 install-authoring 클러스터가 rate-limit으로 유실되어 캐시 재개로 보완했으나 캐시 접두사 단절로 사실상 독립 2라운드(후보 25 → 확정 8 / 기각 17)가 실행됨 — 두 라운드의 교차 대조가 최종 판정.

- **채택(독립 10)**: §3.4 표 — R1: AC-1a·IA-1·HG-3 / R2: PL-3·AC-1b·PL-1 / R4: KN-2·KN-3·ST-3·KN-4.
- **채택(흡수 4)**: G1-chk(stop_hook_active), ST-1(atomic write → §4.4-1/-3), AC-4(상호참조 → §3.2 skill-contract), PR-1(재수렴 신호 → §4.4-8).
- **결정 항목(1)**: MQ-2(verify 산출물 JSON 격상) — 상반된 두 독립 검증이 공존해 R2 plan에서 결정(§3.3 각주 정정 완료).
- **기각 대표 사례**(재검토 방지 — 전체는 워크플로 저널): PreCompact wiki 배너(2라운드가 1라운드 확정을 뒤집음 — pull 방식 pre-commitment라 실패모드 부재), evidence-tag grammar(소비자 없는 생산자 + single-careful 도메인에 병렬 취합 부재), 세션 ownership envelope(`.omd/<slug>/` 경로가 이미 네임스페이스 격리), 해시 폴백 슬러그(기존 "사용자 ASCII 슬러그 확인" 정책과 이중 해법), withWikiLock(single-careful라 불필요), MCP injection hygiene(대상 인프라 부재 — wiki_query MCP 전환 시 R5+ 조건부), docs-revise 하드 카운터(단일 세션 루프라 위협 부재), capture 자동화 재상신(§4.5 중복).
- **방법론 관찰**: 검증관들이 출처 파일:줄 실물 대조를 통해 1라운드 확정 2건을 2라운드에서 뒤집었고(더 강한 도메인 근거), 검증 불가 판정 1건은 교차 지원(이전 리서치 에이전트에게 출처 확인 위임)으로 정정됨 — "REFUTE 기본값 + 실물 대조" 게이트가 채택 후보의 약 2/3를 걸러냄. 워크플로 저널: 세션 transcript `subagents/workflows/wf_ad99f459-150/journal.jsonl`.
