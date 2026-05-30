---
name: docs-build
description: |
  승인된 아웃라인으로 실제 문서 산출 — 포맷 지식 카드를 읽고 렌더 엔진(python-pptx/docx/hwpx)을
  직접 구동. 인라인/블록 수식 지원. 원본 in-place 금지(새 파일+버전 스냅샷). 기존 ppt-* 스킬을
  호출하지 않고 OMD 가 직접 빌드(rebuild). OMD 4단계.
  Triggers: 만들어줘, 산출, 생성, 빌드, .pptx 만들어, .docx 만들어, 발표자료 생성,
  document build, generate document, 수식 넣어, 슬라이드 생성
---

# docs-build — 산출 (4단계)

<Purpose>
승인된 아웃라인을 실제 .pptx/.docx/.hwpx 로 산출한다. references/formats/<format>.md 카드를 읽고 렌더 엔진을 직접 구동 — 기존 ppt-* 를 호출하지 않는다(OMD = rebuild). **수식**은 카드가 VERIFIED 표시한 경로로만.
</Purpose>

<Use_When>
- 아웃라인이 승인됐고 이제 산출물을 만들 때
- 기존 문서를 *수정*할 때 (revision — 버전 스냅샷 후 작업)
</Use_When>

<Do_Not_Use_When>
- 구조가 아직 안 정해졌을 때 → docs-plan 먼저
- 단순히 "어때?" 검토만 원할 때 → docs-inspect
</Do_Not_Use_When>

<Gate>
**게이트 2 — 콘텐츠 확정.** 빌드 후 builder 의 sanity 렌더(PNG)를 사용자에게 보여 내용이 맞는지
확인. (만듦새 판정 아님 — 그건 inspect/verify.)
</Gate>

<Format_Knowledge>
포맷별 도구·함정·수식·버전정책은 **references/formats/<format>.md 카드가 단일 진실**. 이 스킬·에이전트에 복제하지 말고 카드를 읽어라:
- pptx → references/formats/pptx.md (python-pptx, 수식 = matplotlib PNG only[soffice가 OMML 미렌더], 버전 스냅샷)
- docx → references/formats/docx.md (python-docx, 수식 2경로[OMML 편집가능 VERIFIED + matplotlib 폴백], 헤더/PAGE 필드/한글폰트 함정)
- xlsx → references/formats/xlsx.md (openpyxl/xlsxwriter 라우팅, `<v>0</v>` 수식캐시 함정, 구조검증 게이트[PNG 정독 아님])
- hwpx → references/formats/hwpx.md (stub)
</Format_Knowledge>

<Steps>
1. doc-builder 를 dispatch (아웃라인 + analyzer/standardize 의 design system 전달):
   `Task(subagent_type="oh-my-docs:doc-builder", ...)`
2. builder 가 카드를 읽고 → (revision 이면) `.omd/<slug>/versions/` 스냅샷 → 빌드 스크립트 → 산출 → 수식(VERIFIED 경로) → 자체 PNG sanity 렌더(`.omd/<slug>/renders/current/`).
3. 산출물(outputs/<slug>/current.<ext>) + sanity PNG 를 게이트 2 로 제시 → 확인.
</Steps>

<Output>
사용자가 보는 최종본은 `outputs/<slug>/current.<ext>` 하나. 버전 스냅샷(큰 수정 시)·sanity 렌더·빌드 노트는 작업장 `.omd/<slug>/`(`versions/`·`renders/current/`·`build-notes.md`)에. 경로 규약은 `references/output-layout.md`가 SSOT. inspect/verify 로 넘김.
</Output>
