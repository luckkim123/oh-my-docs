---
name: docs-verify
description: |
  완성 문서 최종 검증 — 파일 무결성(zip CRC/엔진 파싱/soffice 변환/dangling rels/orphan master 5/5)
  + 전수 PNG 정독 + 아웃라인 대비 완전성 → 명확한 PASS/FAIL 게이트. 산출한 컨텍스트가 자기 승인
  못 함(self-approval 금지). OMD 최종 단계.
  Triggers: 최종 검증, 이거 문제없어, 최종본 확인, 무결성, 검수, 납품 전 확인,
  verify document, final check, integrity, 복구 다이얼로그, 깨졌나
---

# docs-verify — 최종 검증 (총괄 게이트)

<Purpose>
완성 문서가 *파일로서*(복구 다이얼로그 없이 열림) 그리고 *산출물로서*(전 슬라이드 정상) 기준을 넘는지 증거로 판정한다. inspect 의 형성적 조언과 달리 명확한 PASS/FAIL.
</Purpose>

<Use_When>
- 문서를 최종본/납품본으로 확정하기 전
- docs-pilot 의 마지막 게이트
- 독립 진입: "이거 문제없어?" 최종 검수만 원할 때
</Use_When>

<Do_Not_Use_When>
- 개선점 조언이 필요할 때 → docs-inspect (형성적)
- 산출물이 없을 때 → docs-build 먼저
</Do_Not_Use_When>

<Gate>
**게이트 3 — 최종.** 무결성 5/5 + 전수 정독 + 필수섹션 완전 → PASS. 하나라도 실패 = FAIL.
4/5 는 FAIL (복구 다이얼로그 잔존).
</Gate>

<Checks>
무결성 정의 = references/formats/<format>.md, 3축 = references/rubrics/ppteval.md.
zip CRC · 엔진 파싱 · soffice 변환 · dangling relationships · orphan slideMaster (5종 전부).
</Checks>

<Steps>
1. doc-verifier 를 dispatch (아웃라인 + 산출물 경로 전달):
   `Task(subagent_type="oh-my-docs:doc-verifier", ...)`
2. verifier 가 무결성 5종 직접 실행 + ≥150dpi 전수 정독 + 아웃라인 대비 완전성 + versions/ 개수.
3. **style-spec 메타 정합 (읽기전용, H10)** — `.omd/wiki/convention/lab-style-spec.md`(또는 `<key>-style-spec.md`)에
   self-specialization 메타가 있으면 무결성만 확인: `specificity` ∈ [0,1] 이고 `(origin∈{inductive,learned} 수)/(활성 기본값 수)`
   와 일치하는가, `learned` origin 마다 `learned_refs` provenance 가 있는가(§6.C silent 변경 금지).
   불일치 시 **경고(WARN)만** — FAIL 아님. ⚠️ verify 는 메타를 **읽기만**, 절대 수선 안 함(수선은 docs-learn 사람 게이트 몫).
4. PASS/FAIL 증거표를 게이트 3 으로 제시(메타 WARN 은 FAIL 에 안 들어감). FAIL 이면 docs-build 로 되돌려 수정 루프.
5. versions/ 가 임계 초과면 구버전 정리 권유.
</Steps>

<Output>
PASS/FAIL 판정 + 무결성 증거표 + 전수 정독 결과 + 완전성 표 + style-spec 메타 PASS/WARN. APPROVE/REQUEST_CHANGES.
</Output>

<Separation>
산출한 컨텍스트가 자기 승인 못 함(self-approval 금지). verify 는 authoring 과 분리된 lane 에서만.
</Separation>
