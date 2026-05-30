---
name: docs-translate
description: |
  자료 재목적화 — 같은 콘텐츠를 다른 언어·톤·청중으로 변환(KO 디펜스→EN 학회 등). 내용 보존이
  최우선: 출처·수치·주장 왜곡 금지(citation-bound 가드레일). 단계중심(포맷은 변수).
  Triggers: 영어로 바꿔, 번역, 재목적화, 학회용으로, 톤 바꿔, KO를 EN으로,
  translate document, repurpose, retarget, localize, 다른 청중용
---

# docs-translate — 자료 재목적화 (단계)

<Purpose>
완성 자료를 다른 언어·톤·청중으로 재목적화한다 (예: KO 디펜스 → EN 학회 발표). 새 내용을 만드는 게 아니라 *기존 콘텐츠의 표현을 옮긴다* — 사실·수치·출처는 불변.
</Purpose>

<Use_When>
- 같은 발표를 다른 언어·청중용으로 다시 쓸 때 (KO→EN, 디펜스 톤→학회 톤)
- 한 자료를 여러 venue 로 재활용할 때
</Use_When>

<Do_Not_Use_When>
- 새 내용을 *추가/생성* 하는 거면 → docs-build (translate 는 표현만 옮김)
- 단순 포맷 변환이면 → docs-convert
</Do_Not_Use_When>

<Guardrails_Citation_Bound>
⚠️ **재목적화는 hallucination 위험 지점.** 표현을 옮기면서 사실이 미끄러지기 쉽다. 하드룰:
- **수치·출처·인용은 원문 그대로 유지** — 번역 과정에서 숫자나 citation 을 바꾸거나 "매끄럽게" 보정 금지.
- **주장 강도 보존** — 원문이 "suggests" 면 번역도 "suggests", "proves" 로 격상 금지.
- **새 주장 삽입 금지** — 청중이 바뀌어도 없던 결론을 추가하지 않음.
- **원문 대조 필수** — 각 슬라이드/섹션 번역 후 원문과 사실 일치 확인 (doc-verifier 의 spec 완전성 lane).
- 논문 등 엄격 citation 문서는 **병렬 처리 금지**, 단일 신중 (user-scope 룰).
</Guardrails_Citation_Bound>

<Gate>
**게이트 — 사실 보존 확인.** 재목적화 후 원문 대비 수치·출처·주장강도가 보존됐는지 대조 제시 →
사용자 확인. 톤·언어만 바뀌고 사실은 불변임을 보여야 함.
</Gate>

<Steps>
1. 원문 자료를 doc-analyzer 로 인벤토리 (사실·수치·출처·주장 목록 추출):
   `Task(subagent_type="oh-my-docs:doc-analyzer", ...)`
2. 목표 언어·톤·청중 확정 (모호하면 docs-intake 식 질문).
3. doc-builder dispatch: 표현만 재목적화 (위 가드레일 전달, 사실 목록 고정):
   `Task(subagent_type="oh-my-docs:doc-builder", ...)`
4. doc-verifier dispatch: 원문 대비 사실 보존 대조 (수치/출처/주장강도) + 무결성:
   `Task(subagent_type="oh-my-docs:doc-verifier", ...)`
5. 사실 보존 대조표를 게이트로 제시 → 확인.
</Steps>

<Output>
outputs/<slug>/<name>_<lang>.<ext> + 사실 보존 대조표(원문↔재목적화 수치/출처/주장 일치). 원문 보존. (재목적화본은 `current.<ext>`와 별개 산출 패밀리 — 같은 outputs/<slug>/ 폴더에 언어 접미사 파일로, `current.<ext>`를 덮어쓰지 않는다.)
</Output>
