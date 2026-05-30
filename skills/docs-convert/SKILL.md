---
name: docs-convert
description: |
  문서 포맷·납품본 변환 단계 — .pptx/.docx→배포 PDF, .md→docx, .hwp→hwpx 정규화 게이트.
  렌더 엔진(soffice/pandoc)을 조율할 뿐 변환기를 새로 짜지 않는다. 검증된 경로만 사용,
  미검증은 명시. 단계중심(포맷은 변수).
  Triggers: PDF로 변환, 납품본, 변환해줘, pptx를 pdf로, hwp 변환, 포맷 바꿔,
  convert document, export pdf, to pdf, 배포용
---

# docs-convert — 포맷/납품본 변환 (단계)

<Purpose>
완성 문서를 다른 포맷·납품본으로 변환한다. .pptx/.docx → 배포 PDF, .md → docx, .hwp → hwpx 정규화. 변환기를 새로 짜지 않고 검증된 엔진(soffice/pandoc)을 조율 — references/conversions.md 가 어느 변환이 검증됐는지의 단일 진실.
</Purpose>

<Use_When>
- 완성 deck/문서를 배포 PDF 로 뽑을 때
- .hwp 입력을 OMD 가 다룰 수 있는 hwpx/docx 로 정규화할 때 (변환 게이트)
- .md 초안을 .docx 로 올릴 때
</Use_When>

<Do_Not_Use_When>
- 새 문서를 *만드는* 거면 → docs-build
- .hwp 를 직접 *수정/쓰기* 하려는 거면 → 불가 (macOS 순수 파이썬 한계). 정규화 게이트만.
</Do_Not_Use_When>

<Conversion_Knowledge>
references/conversions.md = 변환 매트릭스의 단일 진실. 검증 상태(VERIFIED/UNVERIFIED/GATE) 확인 후 사용:
- **.pptx → .pdf** = VERIFIED ✓ (soffice). 배포본 기본 경로.
- **.hwp → hwpx/docx** = GATE (macOS 순수 파이썬 불가, 수동 export). 직접 쓰기 금지.
- 나머지는 UNVERIFIED — 첫 사용 시 실제 변환+출력 확인 후 매트릭스 갱신.
</Conversion_Knowledge>

<Gate>
**게이트 — 변환 확인.** 변환 후 출력 파일 실재 + 비자명 크기 확인. PDF 면 첫 페이지 PNG 렌더로
내용 보존 눈 확인. 원본은 절대 변형 안 함 (새 확장자로 outputs/<slug>/ 에).
</Gate>

<Steps>
1. references/conversions.md 에서 요청 변환의 상태 확인. GATE/불가면 사용자에게 알리고 멈춤.
2. doc-builder 를 dispatch (변환 = 엔진 구동이므로 builder lane):
   `Task(subagent_type="oh-my-docs:doc-builder", ...)`  — "convert, not author" 명시.
3. builder 가 검증 경로로 변환 → 출력 파일 실재+크기 확인.
4. (PDF) 첫 페이지 렌더로 내용 보존 확인 → 게이트 제시.
5. 새로 검증된 변환이면 conversions.md 매트릭스 갱신 (VERIFIED ✓).
</Steps>

<Output>
outputs/<slug>/<name>.<new-ext> + 변환 노트(엔진/exit/크기). 원본 보존. (변환·납품본은 `current.<ext>`와 별개 산출 패밀리 — 같은 outputs/<slug>/ 폴더에 새 확장자 파일로 두되, 빌드 산출물 `current.<ext>`를 덮어쓰지 않는다.)
</Output>
