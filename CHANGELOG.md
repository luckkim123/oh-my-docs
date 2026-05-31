# Changelog

All notable changes to oh-my-docs (omd).

> **버저닝 방침**: omd 는 의도적으로 **commit-SHA 버저닝**을 쓴다(개별 릴리스 번호 없음).
> 이 파일은 *계약(contract) 변경 이력*만 추적한다 — hook 의 emit 포맷처럼 다른
> 컴포넌트(omha·세션 LLM)가 의존하는 표면이 바뀌면 여기 기록한다. 일반 콘텐츠
> 변경은 git 로그가 SSOT. OMS(oh-my-scholar)의 CHANGELOG 톤과 통일.

## [Unreleased]

### Added
- **2계층 wiki — `wiki_query` 계약을 로컬+전역 ascent 병합으로 확장** (oms `e47ab44` 의
  2계층 ascent wiki 를 omd 도메인으로 ADAPT backport). `wiki_query(category)` 구현이 로컬
  `.omd/wiki/` + 가장 가까운 상위 `.omd/wiki/`(전역 레벨, ascent 로 발견 — git 의 `.git` 찾기
  방식)를 병합하고 `[wiki:local]`/`[wiki:global]` 출처 태깅한다. ⚠️ **호출부 시그니처 불변** —
  ascent·병합·태깅은 전부 추상함수 구현 안에 갇혀 `doc-inspector` pre-commitment 는 한 줄도 안
  바뀐다(미래 MCP 교체점도 그대로). 절대경로·env·XDG 0개(work-root 상대). 상위 `.omd/` 부재 시
  graceful 빈 목록. 갱신: `references/wiki/README.md`·`references/learning-protocol.md`(§1.4
  "Two wiki levels" 신설)·`agents/doc-inspector.md`·`skills/docs-pilot/SKILL.md`(Step 7)·
  `skills/docs-learn/SKILL.md`(§4b 로컬→전역 승급 경로). 회귀가드 `tests/test_wiki_two_level.py`.
  ⚠️ **omd 도메인 변형(oms 통째복사 아님)**: ① oms 전역 전용 `history/` 카테고리 **드롭**(omd 엔
  init·문서-dedup 수요 없어 dead) ② oms 의 citation 전역금지 → omd 는 **document content
  (text·claims·numbers·sources) 전역 영구금지**(§6.F content-preservation 의 전역 확장) ③ **cross-
  project 기밀 격리 게이트 신설**(oms 무 — 전역 wiki 는 다중 프로젝트 공유라 식별가능한 프로젝트 고유
  content 는 전역금지·로컬만, 추상 form 규칙만 승급, `docs-learn` §4b 가 스크럽 강제).
- **`docs-learn` 를 plugin.json skills 에 등록** (드리프트 수정): 디스크엔 있으나 plugin.json
  미등록이라 배포 시 로드 안 되던 것을 보정(2계층 wiki 의 로컬→전역 승급 소유 스킬이라 누락 시
  §4b 가 dead ship). 회귀가드 `tests/test_plugin_integrity.py` 로 skills↔디렉토리 1:1 드리프트 차단.

### Changed
- **`references/omc-backport-analysis.md` §4 신설 — omp 0.2.0 역방향 backport 검토(채택 0).**
  형제 omp 가 0.2.0 에 추가한 5종(content_conventions·content audit·dead-link·CONVENTIONS.md·
  specificity content 항)을 omd 로 역방향 backport 할지 적대 검증(omd 실소스 대조) → 전부 REJECT.
  omd 는 바이너리 office 산출물 생성 파이프라인이라 rules.json 정규식 audit 루프·body/frontmatter
  scope 가 referent 상실, content 검증은 PPTEval 3축 rubric 이 담당. specificity content 항은 omd
  가 §3 제외표·learning-protocol §5 H6("no numeric weighted sum")에서 *이미 명시 거부*한 범주.
  "역방향 채택 0" 을 영속 기록해 재검토 반복 방지. 코드 변경 0 — 문서만.
- **xlsx 포맷을 라우팅 hook 계약에 추가** (`hooks/route_emit.py`, UserPromptSubmit): FORMAT
  슬롯이 `pptx|docx|hwpx` 뿐이라 xlsx 작업이 라우팅에 인지되지 않던 것을 수정 →
  `pptx|docx|xlsx|hwpx`. 본문 포맷 목록·STAGE 줄 양쪽 갱신. 회귀테스트
  `test_context_lists_formats` 에 xlsx 추가(11 passed). stdlib only·fail-open 유지.
- **docs-build 카드 목록 갱신** (`skills/docs-build/SKILL.md`): docx 를 "stub" → 완성으로,
  xlsx 추가, pptx 수식 정책을 "matplotlib PNG only(soffice OMML 미렌더)"로 정정.
- **라우팅 hook 계약 확장** (`hooks/route_emit.py`, UserPromptSubmit): STAGE 카탈로그에
  `revise` 토큰 추가 — `docs-revise` 스킬이 실재하나 STAGE 목록에서 누락돼 있던 것을 수정
  (`intake|standardize|plan|build|inspect|verify|revise|docs-pilot`). 또한 Deliberate
  (디펜스·심사·외부 공식 발표) 트리거 시 `docs-plan --consensus`(RALPLAN-DR) 발동을 한 줄
  근거에 밝히라는 단서를 주입. stdlib only·fail-open 패턴 유지.

### Added
- **docx 포맷 카드 완성** (`references/formats/docx.md`, STUB→full): python-docx 1.2.0 엔진,
  수식 2경로(**OMML 편집가능 path A = soffice 렌더 VERIFIED**[caveat: `\hat` accent·`\sum` □],
  matplotlib PNG path B 폴백), 헤더/풋터 3규칙(+#1424 함정), PAGE 필드(simple PAGE = soffice
  렌더 VERIFIED), 한글폰트, `paragraph.text` getter안전/setter파괴, JPEG render recipe.
- **xlsx 포맷 카드 신설** (`references/formats/xlsx.md`): openpyxl(수정)/xlsxwriter(생성) 라우팅,
  `<v>0</v>` 수식캐시 함정(VERIFIED 실측 — `--convert-to`로 재계산 안 됨, calculateAll 매크로 필요),
  구조검증 게이트(PNG 정독 아님 — 스프레드시트 특성), openpyxl 차트 load 손실·app.xml 함정.
- **MCP/공식skills backport 분석 문서** (`references/mcp-skills-backport-analysis.md`, 신설):
  Office MCP 8종(채택 안 함, python 직접구동이 이미 그 엔진) + Anthropic 공식 Agent Skills(패턴
  차용 원천)의 채택/제외 매핑 + 포맷별 수식 렌더 실측 매트릭스 + diff 기준.
- **라우팅 hook 회귀 테스트** (`tests/test_route_emit.py`, 신설): omd 는 그동안 `tests/`가
  없었으나 hook 은 *계약*이라 변경 시 회귀 검증이 필요 → 9건 신설(UserPromptSubmit emit·
  STAGE contract·8단계 열거(revise 포함)·3포맷 열거·format 카드 권위·`--consensus` 근거·
  레이블 충돌 없음(STAGE(docs)↔STAGE(paper)↔ROUTE)·stdlib only·fail-open).
- **OMC backport 분석 문서** (`references/omc-backport-analysis.md`, 신설): deepen·consensus·
  critic 4기법 등이 OMC 4.14.4 의 무엇에서 왔고 무엇을 제외했는지 영속 기록 — OMC 업데이트 시
  갱신 판단 기준.

### Verification
- `pytest tests/` — 11 passed (route_emit 회귀, xlsx 포맷 추가 포함).
- 두 hook 모두 `python3 -c "import ast; ast.parse(...)"` 통과 + 실행 시 valid JSON emit
  (`revise`·`--consensus`·`xlsx` 포함 확인).
- **수식·함정 실측**(2026-05-31): docx OMML soffice 렌더 PNG 눈 확인(PoC1·2), pptx OMML 빈칸
  재확인(PoC3), docx PAGE 필드 "2쪽" 렌더 확인(PoC4), xlsx `<v>0</v>` 캐시 + `--convert-to`
  재계산 안 됨 확인(PoC5b). 카드의 모든 VERIFIED 주장은 실제 렌더 PNG 근거.
