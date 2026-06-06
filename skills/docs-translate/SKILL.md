---
name: docs-translate
description: |
  Content repurposing — convert the same content to a different language, tone, or audience (KO defense → EN conference, etc.). Content preservation is
  the top priority: do not distort sources, figures, or claims (citation-bound guardrails). Stage-centric (format is a variable).
  Triggers: 영어로 바꿔, 번역, 재목적화, 학회용으로, 톤 바꿔, KO를 EN으로,
  translate document, repurpose, retarget, localize, 다른 청중용
---

# docs-translate — Content Repurposing (stage)

<Purpose>
Repurpose a finished asset for a different language, tone, or audience (e.g., KO defense → EN conference talk). This does not create new content — it *moves the expression of existing content*; facts, figures, and sources stay unchanged.
</Purpose>

<Use_When>
- Rewriting the same talk for a different language or audience (KO→EN, defense tone → conference tone)
- Reusing one asset across multiple venues
</Use_When>

<Do_Not_Use_When>
- If you are *adding/generating* new content → docs-build (translate only moves the expression)
- If it is a simple format conversion → docs-convert
</Do_Not_Use_When>

<Guardrails_Citation_Bound>
⚠️ **Repurposing is a hallucination risk point.** Facts slip easily while moving expression. Hard rules:
- **Keep figures, sources, and citations exactly as in the original** — do not change numbers or citations or "smooth them over" during translation.
- **Preserve claim strength** — if the original says "suggests", the translation also says "suggests"; do not escalate to "proves".
- **No new claims** — do not add conclusions that were not there, even when the audience changes.
- **Original cross-check required** — after translating each slide/section, verify factual consistency against the original (doc-verifier's spec-completeness lane).
- For strict citation documents such as papers, **no parallel processing**, single careful pass (user-scope rule).
</Guardrails_Citation_Bound>

<Gate>
**Gate — fact-preservation check.** After repurposing, present a cross-check of figures, sources, and claim strength against the original →
user confirmation. Must show that only tone and language changed while facts stayed unchanged.
</Gate>

<Steps>
1. Inventory the original asset with doc-analyzer (extract the list of facts, figures, sources, claims):
   `Task(subagent_type="oh-my-docs:doc-analyzer", ...)`
2. Fix the target language, tone, and audience (ask docs-intake-style questions if ambiguous).
3. Dispatch doc-builder: repurpose expression only (pass the guardrails above, fix the fact list):
   `Task(subagent_type="oh-my-docs:doc-builder", ...)`
4. Dispatch doc-verifier: cross-check fact preservation against the original (figures/sources/claim strength) + integrity:
   `Task(subagent_type="oh-my-docs:doc-verifier", ...)`
5. Present the fact-preservation cross-check table as the gate → confirm.
</Steps>

<Output>
outputs/<slug>/<name>_<lang>.<ext> + fact-preservation cross-check table (original↔repurposed match on figures/sources/claims). Original preserved. (The repurposed version is a separate output family from `current.<ext>` — placed in the same outputs/<slug>/ folder as a language-suffixed file, never overwriting `current.<ext>`.)
</Output>
