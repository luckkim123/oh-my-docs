---
name: docs-verify
description: |
  Final verification of a completed document — the card-defined verify gate (office: file integrity zip CRC / engine parsing / soffice conversion / dangling rels / orphan master 5/5
  + exhaustive PNG read-through; text genres: the card's exit-code chain) + completeness against the outline → a clear PASS/FAIL gate. The context that produced the output cannot
  self-approve (no self-approval). OMD's final stage.
  Triggers: 최종 검증, 이거 문제없어, 최종본 확인, 무결성, 검수, 납품 전 확인,
  verify document, final check, integrity, 복구 다이얼로그, 깨졌나
---

# docs-verify — Final Verification (overall gate)

<Purpose>
Judge, with evidence, whether a completed document clears the bar *as a file* (opens without a recovery dialog) and *as a deliverable* (every slide is correct). Unlike inspect's formative advice, this yields a clear PASS/FAIL.
</Purpose>

<Use_When>
- Before finalizing a document as the final / deliverable version
- The last gate of docs-pilot
- Standalone entry: when you only want a final "Is this OK?" inspection
</Use_When>

<Do_Not_Use_When>
- When you need improvement advice → docs-inspect (formative)
- When there is no output yet → docs-build first
</Do_Not_Use_When>

<Gate>
**Gate 3 — final.** Every item of the card-defined verify gate passes + required sections complete → PASS. Any single failure = FAIL. Office formats: integrity 5/5 + exhaustive ≥150dpi read-through — 4/5 is FAIL (recovery dialog remains). Text genres (repo-docs): the card's deterministic exit-code chain (section order, links, lint, dates, placeholder scan) + fresh-read. Missing engine → `UNVERIFIED (engine unavailable)` per D3, never a silent PASS.
</Gate>

<Checks>
The gate definition lives in references/formats/<format>.md (single source of truth); the qualitative axes in the format's rubric card (office: references/rubrics/ppteval.md; repo-docs: references/rubrics/repo-docs-rubric.md).
Office integrity = zip CRC · engine parsing · soffice conversion · dangling relationships · orphan slideMaster (all 5).
</Checks>

<Steps>
1. Dispatch doc-verifier (passing the outline + output path):
   `Task(subagent_type="oh-my-docs:doc-verifier", ...)`
2. The verifier directly runs the card-defined verify gate (office: the 5 integrity checks + ≥150dpi exhaustive read-through; text genres: the exit-code chain with logs captured to .omd/<slug>/verify-runs/) + completeness against the outline + versions/ count.
3. **style-spec meta consistency (read-only, H10)** — if `.omd/wiki/convention/lab-style-spec.md` (or `<key>-style-spec.md`) has
   self-specialization meta, check only its integrity: is `specificity` ∈ [0,1] and does it match `(count of origin∈{inductive,learned})/(count of active defaults)`,
   and does every `learned` origin have `learned_refs` provenance (no §6.C silent change)?
   On mismatch, emit a **warning (WARN) only** — not a FAIL. ⚠️ verify only **reads** the meta, it never repairs it (repair is docs-learn's human-gate job).
4. Present the PASS/FAIL evidence table at gate 3 (a meta WARN does not count toward FAIL). On FAIL, return to docs-build for the fix loop.
5. If versions/ exceeds the threshold, suggest cleaning up old versions.
</Steps>

<Output>
PASS/FAIL verdict + integrity evidence table + exhaustive read-through results + completeness table + style-spec meta PASS/WARN. APPROVE/REQUEST_CHANGES.
</Output>

<Separation>
The context that produced the output cannot self-approve (no self-approval). verify runs only in a lane separate from authoring.
</Separation>
