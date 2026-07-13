---
name: docs-inspect
description: |
  Formative review of an in-progress document — ranks improvements along the
  format's rubric card axes (office: PPTEval Content/Design/Coherence). This is advice while changes
  are still cheap, not a pass/fail verdict (that's docs-verify).
  Triggers: 이거 어때, 검토해줘, 발표자료 봐줘, 피드백, 개선점, 지금 상태 어때,
  review document, critique, inspect, 슬라이드 검토, 보완할 점
---

# docs-inspect — In-Progress Review (Formative)

<Purpose>
Critiques an in-progress document formatively. Presents *ranked* improvements along the format's rubric card axes (office: PPTEval 3 axes) — advice at the stage where change is still cheap. Separates and elevates what ppt-edit only verified into active critique.
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
The format's rubric card is the single source of truth — office: references/rubrics/ppteval.md (3 axes: Content message·evidence·density / Design font·color·overflow at ≥150dpi / Coherence arc·transitions); repo-docs: references/rubrics/repo-docs-rubric.md. Lens composition is not fixed at 3 — it covers exactly the qualitative axes the format's verify gate does NOT already check mechanically (PS-3).
</Rubric>

<Steps>
**Default (small deck)** — single inspector:
1. Dispatch doc-inspector:
   `Task(subagent_type="oh-my-docs:doc-inspector", ...)`
2. The inspector gathers evidence the way the rubric card prescribes (office: render all slides at ≥150dpi and read them; text genres: fresh-read every file) → ranks per-axis improvements by impact.

**Multi-lens (large deck / precise review)** — one lens per rubric-card axis, in parallel (ralplan critic pattern):
1. Dispatch doc-inspector **in parallel, one per axis of the format's rubric card** (office: Content / Design / Coherence; repo-docs: the card's qualitative axes):
   `Task(subagent_type="oh-my-docs:doc-inspector", ...)` × N (axis specified via prompt)
2. Merge the per-axis lens results, integrating them by impact rank with no per-axis conflicts.

**Common**:
3. Present the ranked improvement list to the user (advice — not a verdict).
</Steps>

<Multi_Lens_When>
Multi-lens is for a large deck (20+ slides) or when a precise review is needed. For a small deck, a single inspector covers the rubric card's axes in one pass (office: 3) — going per-axis is overkill. Either way, the inspector is in a different lane from the builder (no self-approval).
</Multi_Lens_When>

<Output>
A ranked improvement list (each item: axis / location / finding / recommended fix). Does not issue a pass verdict — that's for verify.
</Output>

<Separation>
inspect never says "done/approved". Formative (improvements) and summative (pass line) are different lanes,
and neither one lets the same context that produced the build self-approve it.
</Separation>
