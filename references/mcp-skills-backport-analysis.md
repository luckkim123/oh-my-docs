# MCP / Official-Skills Backport Analysis — oh-my-docs (omd)

omd 의 포맷 카드(`references/formats/*.md`)와 빌드 규율은 **외부 문서 자동화 생태계**(Office MCP
서버 + Anthropic 공식 Agent Skills)의 검증된 패턴을 차용해 진화한다. 그 생태계가 업데이트되면
*무엇이 바뀌었고 omd 를 갱신해야 하는지* 판단할 영속 기준이 필요하다. 이 문서가 그 "diff 기준"을
자체 보관한다. (sibling: `references/omc-backport-analysis.md` — OMC 하네스 패턴 backport.)

> **이 문서는 배포 plugin 의 references/ 라 개인 환경에 비의존이다.** 외부 repo 는 공개 URL 로만
> 적고, 특정 머신의 절대경로·사용자 데이터는 박지 않는다.

---

## §1. 조사 스냅샷 (2026-05-31) — 생태계 지형

### 결론: omd 는 MCP 를 붙이지 않는다 (확정)

- 조사한 Office MCP 서버의 **백엔드 엔진이 거의 전부 python-pptx / python-docx / openpyxl** —
  MCP 는 omd 가 이미 직접 구동하는 라이브러리의 JSON-RPC 래퍼다.
- omd 는 단일 하네스에서 에이전트가 Bash 로 라이브러리를 직접 구동 → MCP 를 얹으면 IPC·서버기동
  오버헤드만 추가. MCP 실익("다중 클라이언트 배포")은 omd 자체용도라 해당 없음.
- 따라서 **패턴만 차용**(연결 아님). 이는 omd 의 "라이브러리 직접 구동" 철학과 일치한다.

### 조사된 MCP 서버 (참고용 — 채택 안 함, 패턴만)

| 포맷 | 대표 서버 | ★ | 엔진 | omd 가 본 것 |
|:---|:---|:---|:---|:---|
| pptx | GongRzhe/Office-PowerPoint-MCP-Server | 1.7K | python-pptx | 11-모듈/34-도구 API 분류 |
| docx | SecurityRonin/docx-mcp | — | OOXML 직접조작 | python-docx 못하는 것 우회 설계 |
| docx | meterlong/mcp-doc | 186 | python-docx | 편집 시 원본 스타일 보존 |
| xlsx | haris-musa/excel-mcp-server | 3.9K | openpyxl | 엔진 선택의 레퍼런스 |
| 변환 | microsoft/markitdown | 132K | MarkItDown | Office→md intake(미채택) |

⚠️ **MCP 서버 8종 전부 수식(OMML/math) 네이티브 지원 없음** — omd 의 docx OMML 경로가 차별점.

### ⭐ Anthropic 공식 Agent Skills (github.com/anthropics/skills) — 진짜 차용 원천

공식 `pptx`/`docx`/`xlsx` 스킬은 omd 와 **같은 계열**(라이브러리를 VM 안 bash 로 직접 구동).
source-available 라 코드/패턴을 직접 대조했다. **단 omd 와 다른 점**:
- 신규 생성: pptx=**pptxgenjs(Node)**, docx=**docx-js(Node)**. omd 는 python 직접구동이라 **Node
  엔진은 비차용**, 안전규칙·QA 레시피·XML 편집 규율만 차용.
- 기존 수정: `unpack → XML edit → pack --original`(스키마 검증). omd 는 python-docx 직접빌드.

---

## §2. diff 기준 (생태계 업데이트 시 재검토)

- **공식 skills 는 CHANGELOG 가 약함** → 다음 업데이트 시 아래 §3 *채택* 파일들의 diff 를 직접 보고
  omd 카드 갱신 여부를 판단한다:
  - `skills/{pptx,docx,xlsx}/scripts/office/{pack,unpack,soffice}.py`
  - `skills/xlsx/scripts/recalc.py`
  - `skills/*/scripts/office/validators/*.py`
- **MCP 서버**: 채택 안 했으므로 추종 불필요. 단 어떤 MCP 가 **수식 OMML 을 네이티브 지원**하기
  시작하면(현재 전무) omd 의 차별점이 줄어드니 그때 재평가.

---

## §3. 채택·제외 매핑 (Mn = 이 backport 의 내부 작업 ID)

### 채택 (adopt) — 실측 검증 후 카드에 박음

| Mn | 원천 패턴 | omd 적용 (실제 변경) | 검증 |
|:---|:---|:---|:---|
| M1 | 공식 QA 레시피 `soffice→pdf→pdftoppm -jpeg` | docx/xlsx 카드 render recipe = **`-jpeg`**(`-png` 직접변환은 첫장만 = LibreOffice 버그). pptx 카드도 점검 대상 | adv holds |
| M2 | `office/soffice.py` headless env | docx/xlsx 카드에 `SAL_USE_VCLPLUGIN=svp` + sandbox AF_UNIX 소켓 LD_PRELOAD shim 단서 | 소스 확인 |
| M3 | `recalc.py` LibreOffice 매크로 | xlsx 카드: 수식 실제값 = `ThisComponent.calculateAll()` 매크로 필수. **`--convert-to` 만으론 재계산 안 됨**(실측: 0 유지) | **실측 PoC5b** |
| M4 | python-docx OMML 주입 패턴 | docx 카드 수식 path A = `etree.XSLT(mml2omml.xsl)` → `p._element.append`. **issue #320 미해결이지만 omd 가 직접 soffice 렌더 확인** | **실측 PoC1·2** |
| M5 | docx tracked-changes / 단락삭제 규율 | docx 카드 "기존 docx 편집" 절: 저자=Claude, paragraph mark `<w:del/>`, comment.py 예외 | 소스 확인 |
| M6 | xlsx 엔진 분업(openpyxl/xlsxwriter) | xlsx 카드 라우팅 규칙 = 신규=xlsxwriter, 수정=openpyxl(차트 load 손실 경고) | adv holds + 실측 |
| M7 | route_emit 포맷 카탈로그 | `hooks/route_emit.py` 에 **xlsx 포맷 토큰 추가**(STAGE 줄 + 본문). 회귀테스트 `test_context_lists_formats` 에 xlsx 추가 | 11/11 green |

### 제외 (exclude — 사유 포함)

| 패턴 | 제외 사유 |
|:---|:---|
| **MCP 서버 실연결** (모든 8종) | python 라이브러리 직접구동이 이미 그 엔진. IPC 오버헤드만 추가 (§1) |
| **pptxgenjs / docx-js (Node 신규생성)** | omd 는 python-pptx/python-docx 직접빌드. Node 런타임 의존 비차용 |
| **`unpack→pack --original` 파이프라인** (신규생성 경로) | omd 는 rebuild 방식(처음부터 python 생성). pack 검증 규율은 *기존 docx 편집* 시에만 패턴 참고 |
| **markitdown intake (Office→md)** | omd 는 doc-analyzer 가 직접 읽음. 별도 변환 의존 불필요 |
| **pptx native OMML(Path A)** | **실측 재확인: soffice Impress 가 빈칸 렌더**(PoC3). pptx 수식은 matplotlib PNG 유지 |
| **Anthropic Files API / code-execution** | omd 는 로컬 하네스. Anthropic 서버 의존 비차용 |

---

## §4. 포맷별 수식 렌더 — 실측 매트릭스 (omd 고유 발견)

> "코드가 돈다 ≠ soffice 가 렌더한다." 아래는 2026-05-31 실제 .docx/.pptx 생성→soffice→PNG 눈 확인 결과.

| 포맷 | OMML(native) | matplotlib PNG | 카드 정책 |
|:---|:---|:---|:---|
| **docx** (Writer) | ✅ 렌더됨 (caveat: `\hat` accent 어긋남, `\sum`/`\,` □ 빈박스) | ✅ | path A 기본 + 폴백 |
| **pptx** (Impress) | ❌ 빈칸 (body text 소실은 없음) | ✅ | matplotlib PNG only |

→ **포맷마다 수식 정책이 다르다**는 게 핵심. 이걸 모르고 pptx 에 OMML 을 넣으면 빈칸이 나온다.

---

**Analysis snapshot**: 2026-05-31 · 검증 = 실측 PoC 5건(`/tmp/omd_math_poc/`, 비영속) + adversarial
워크플로 9-agent · **isomorphic sibling**: `references/omc-backport-analysis.md`(OMC 하네스 도메인)
