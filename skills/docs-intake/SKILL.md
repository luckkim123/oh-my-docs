---
name: docs-intake
description: |
  Clarify document-work intent — Socratically crystallize a vague request into "what / for whom / why / what tone".
  When it's still hazy what to make (presentation, report, official document, etc.), narrow the intent first. Stage 1 of the OMD harness.
  Triggers: 발표자료 만들건데, 문서 만들어야 하는데 정리가 안 됐어, 뭘 만들지 모르겠어,
  intake, 의중 파악, 문서 기획, document intake, clarify document, 어떤 자료
---

# docs-intake — Intent Clarification (Stage 1)

<Purpose>
Narrow a vague document request into an actionable spec. Crystallize what (format/kind), for whom (audience), why (purpose), and which genre frame — the card defines each genre's intake questions (office: tone preset (defense/conference/lecture); repo-docs: artifact-set scope + genre section preset) — through Socratic questions. The document-side counterpart of OMC deep-interview.
</Purpose>

<Use_When>
- When the user is still hazy about what to make / what tone it should have
- When entering as the first stage of docs-pilot
- Phrases like "정리가 안 됐어" (it's not organized), "뭘 만들지 모르겠어" (I don't know what to make)
</Use_When>

<Do_Not_Use_When>
- When the spec is already crisp (format, audience, tone all decided) → skip straight to docs-plan
- When all that's needed is *revising* an existing document → go directly to docs-build (revision)
</Do_Not_Use_When>

<Gate>
**Gate 0 — Intent locked.** Passes when all of the below are answered; if any is empty, ask:
What (format + document kind) · Who (audience) · Why (purpose) · Tone (preset) · Input (location of source material).

For set genres (repo-docs), additionally lock the **artifact-set scope** before format·kind —
full set / README only / community-health only (the card's set-scope gate); the choice lands
in the D4 manifest `role` fields.
</Gate>

<Steps>
1. Read the request and identify which of the 5 above are empty.
2. If empty, ask **one at a time** (prefer AskUserQuestion multiple choice). Do not fill in by guessing.
3. Once all are answered, dispatch doc-analyzer to grasp the inputs and existing templates:
   `Task(subagent_type="oh-my-docs:doc-analyzer", ...)`
4. **Round 0 — Topology** (after passing Gate 0, isomorphic to scholar-deepen): lock the document's top-level components (commonly 3-6) — sections + message clusters (bundles of core messages to convey) + asset units (figure/table/evidence). Prevents digging one branch depth-first and hiding its siblings.
5. **Qualitative clear/vague judgment per dimension** (4 dimensions, no numbers — qualitative). Judge each dimension **per component** from the Round 0 topology; the dimension's overall verdict is its **weakest component's** verdict — one sharp component never masks a sibling's vagueness (PL-1):
   - **Audience clarity**: Is the audience sharp? (who, what they already know, what they expect)
   - **Message clarity**: Is the one-sentence core message of this presentation sharp? Or blurred by several mixed messages?
   - **Evidence-density clarity**: Is the material (figure/data) backing each message sharp? Any claims left floating?
   - **Constraint clarity**: Are the time, length, delivery-format, and standard-template constraints sharp?
   Each dimension is "clear / vague". If 1 or more are "vague", trigger the corresponding challenge round.
6. **Challenge — ambiguity-resolution rounds** (run a round for each vague dimension, once each — isomorphic to scholar-deepen, document domain). Trigger the rounds below until a dimension judged "vague" in step 5 resolves back to "clear":
   - Round 4 "If this document *didn't exist*, what happens to the audience? Does it have to exist?"
   - Round 6 "If you cut the document in half (slides/sections/files), what do you drop? Just 1 core message?"
   - Round 8 "What *is* this document, really? Where is the naming wobbling?"
   - Each challenge round, record in one line how many Round 0 components survived unrenamed from the previous round (a rename counts as overlap) — the re-convergence signal; low overlap means the ontology is still unstable (PR-1).
   - Soft limits for this round loop (isomorphic to scholar-deepen): early exit if all 4 dimensions are clear at round 3 / soft warning at round 10 (ambiguity isn't resolving fast — reconsider the topic) / hard cap at round 20 (escalate).
7. Present the intent spec + topology + 4-dimension judgment + analyzer inventory to the user as Gate 0 → confirm (proceed to docs-plan only after all dimensions are clear + human confirmation).
</Steps>

<Output>
Intent spec: {format, document kind, audience, purpose, tone preset / genre frame (per the card), input path} + Round 0 topology + 4-dimension qualitative judgment table (clear/vague) + triggered challenge output + analyzer's source inventory.
In a form that the next stage (docs-plan) can take as-is.
</Output>
