---
name: docs-inspect
description: |
  Formative review of an in-progress presentation/document — ranks improvements
  along the PPTEval 3 axes (Content/Design/Coherence). This is advice while changes
  are still cheap, not a pass/fail verdict (that's docs-verify).
  Triggers: 이거 어때, 검토해줘, 발표자료 봐줘, 피드백, 개선점, 지금 상태 어때,
  review document, critique, inspect, 슬라이드 검토, 보완할 점
---

# docs-inspect — In-Progress Review (Formative)

<Purpose>
Critiques an in-progress document formatively. Presents *ranked* improvements along the PPTEval 3 axes — advice at the stage where change is still cheap. Separates and elevates what ppt-edit only verified into active critique.
</Purpose>

<Use_When>
- The user tosses in an in-progress document asking "how is this right now?"
- After docs-pilot output but before verify, when running the improvement loop
- Standalone entry: when you want review only, without going through pilot
</Use_When>

<Do_Not_Use_When>
- When a final pass/fail gate is needed → docs-verify (summative)
- When there is no output yet → docs-build first
</Do_Not_Use_When>

<Rubric>
references/rubrics/ppteval.md is the single source of truth for the 3-axis definitions: Content (message·evidence·placeholder·density) /
Design (font·color·overflow·clipping, ≥150dpi render) / Coherence (arc·transitions·consistency).
</Rubric>

<Steps>
**Default (small deck)** — single inspector:
1. Dispatch doc-inspector:
   `Task(subagent_type="oh-my-docs:doc-inspector", ...)`
2. The inspector renders all slides at ≥150dpi → reads → ranks 3-axis improvements by impact.

**Multi-lens (large deck / precise review)** — 3 lenses in parallel (ralplan critic pattern):
1. Dispatch doc-inspector **3 in parallel**, each focused on a single axis:
   - Lens 1: Content (message·evidence·placeholder·density)
   - Lens 2: Design (font·color·overflow·clipping, ≥150dpi)
   - Lens 3: Coherence (arc·transitions·consistency)
   `Task(subagent_type="oh-my-docs:doc-inspector", ...)` × 3 (axis specified via prompt)
2. Merge the 3 lens results, integrating them by impact rank with no per-axis conflicts.

**Common**:
3. Present the ranked improvement list to the user (advice — not a verdict).
</Steps>

<Multi_Lens_When>
Multi-lens is for a large deck (20+ slides) or when a precise review is needed. For a small deck, a single inspector covers the 3 axes in one pass — 3 lenses is overkill. Either way, the inspector is in a different lane from the builder (no self-approval).
</Multi_Lens_When>

<Output>
A ranked improvement list (each item: axis / location / finding / recommended fix). Does not issue a pass verdict — that's for verify.
</Output>

<Separation>
inspect never says "done/approved". Formative (improvements) and summative (pass line) are different lanes,
and neither one lets the same context that produced the build self-approve it.
</Separation>
