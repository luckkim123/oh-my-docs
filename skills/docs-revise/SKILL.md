---
name: docs-revise
description: |
  Fix-verify loop on an existing document until it gets a verify PASS — "fix it until it passes" for the document in progress. Repeats build fixes and
  verify checks with fresh evidence; if the same defect recurs 3 times, stops and reports (the document counterpart of the ralph pattern). Standalone entry.
  Triggers: 통과까지 고쳐, 문제 다 잡아줘, 계속 고쳐, 검증 통과할 때까지, 반복 수정,
  revise until pass, fix until verified, 수정 루프, 다 고쳐줘
---

# docs-revise — Fix-Verify Loop (document counterpart of ralph)

<Purpose>
Fixes an existing document until verify gives a PASS. Repeats doc-builder (fixes) and doc-verifier (verification) with fresh evidence — not "do your best" but a *guaranteed pass*. The document counterpart of OMC ralph.
</Purpose>

<Use_When>
- When you want an in-progress/finished document "fixed automatically until it passes verify"
- When docs-verify returned FAIL and you want to run those fixes in an automatic loop
- When the user says things like "catch them all", "until it passes"
</Use_When>

<Do_Not_Use_When>
- If you're creating a new document → docs-build (or docs-pilot)
- If you only want improvement advice → docs-inspect (does not modify)
- If it's a citation-bound document → no automatic loop (risk of altering content), apply careful single fixes
</Do_Not_Use_When>

<Execution_Policy>
- **Definition of pass — the document counterpart of ralph's `passes:true`.** The acceptance criteria below must *all* be satisfied for a PASS. If any one falls short, it is not passed (no partial PASS):
  1.–2. The pass definition follows doc-verifier's verdict on the **card-defined verify gate** for the target format, verbatim — office: integrity 5/5 (zip CRC · engine parse · soffice convert · dangling rels · orphan master; 4/5 is a FAIL) + full PNG read-through (≥150dpi, every slide/page including unchanged ones); text genres: the card's deterministic chain + fresh-read. This clause auto-tracks the verifier's card delegation — do not restate gate numbers here (PS-4).
  3. All required outline sections present.
  4. The FAIL defect from the previous round does not recur.
- Each iteration: doc-builder fixes → doc-verifier verifies with fresh evidence (no reuse of prior verification).
- **Do not manufacture a PASS by reducing scope, filling placeholders, or bypassing checks** (ralph: no scope reduction, no deleting tests).
- builder and verifier are different lanes — no self-approval.
- **If the same defect recurs 3 times, stop and report** (fundamental issue — block the infinite loop).
- **boulder never stops (soft extension):** default maximum 5 rounds. On the 5th round, if defects are *decreasing* and it is not the same defect recurring 3 times, you may extend +3 rounds once only (notify the user). If there is no progress, stop and report without extending — no infinite loop.
</Execution_Policy>

<Steps>
1. Diagnose current state: `Task(subagent_type="oh-my-docs:doc-verifier", ...)` → list of FAIL items. Record the previous round's defects (to track recurrence of the same defect).
2. **Loop**:
   a. Fix: `Task(subagent_type="oh-my-docs:doc-builder", ...)` — FAIL items only (snapshot to `.omd/<slug>/versions/` for large fixes).
   b. Re-verify: `Task(subagent_type="oh-my-docs:doc-verifier", ...)` — fresh integrity 5/5 + full read-through.
   c. All acceptance criteria (4 items, 1.–2. combined above) satisfied → terminate (PASS). If any one falls short, check whether it is the same defect recurring:
      - Same defect 3rd time → stop and report "fundamental issue".
      - Max iterations reached → if the boulder extension condition (defects decreasing) is met, extend +3 once, otherwise stop and report.
      - Otherwise → record this round's FAIL defect and go back to (a).
3. Terminate on PASS (criteria 4/4) or a stop condition, presenting the per-round history + final verify evidence table.
</Steps>

<Output>
The PASS'd outputs/<slug>/current.<ext> (the single one the user sees) + iteration history (each round's FAIL → fix summary) + final verify evidence table. Version snapshots in `.omd/<slug>/versions/`.
Or a stop report (same defect 3 times / max iterations exceeded + remaining defects).
</Output>
