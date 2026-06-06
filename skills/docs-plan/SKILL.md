---
name: docs-plan
description: |
  Document structure / outline / storyline design — narrative arc selection + per-slide/section purpose, key message, and required
  asset specs. Lock the structure before producing anything so direction is approved at the cheapest moment. OMD stage 3.
  Triggers: 구조 짜줘, 아웃라인, 어떤 순서로, 발표 흐름, 스토리라인, 목차 설계,
  document outline, structure, narrative, 슬라이드 순서
---

# docs-plan — Structure Design (stage 3)

<Purpose>
Turn the analyzer inventory into a concrete document structure: narrative arc + per-slide/section purpose, key message, and required assets. Lock the structure before producing anything so direction is approved at the *cheapest moment* (when no artifact exists yet).
</Purpose>

<Use_When>
- The intent is clear and now it's time to decide the order/flow for organizing it
- The design stage of docs-pilot
</Use_When>

<Do_Not_Use_When>
- The structure is already given (use the existing outline as-is) → go straight to docs-build
- It's still fuzzy what to make → docs-intake first
</Do_Not_Use_When>

<Modes>
- **`--direct`** (default): single delegation to doc-planner for one outline. Fast and lightweight.
- **`--consensus`**: triggers doc-planner's `<Consensus_RALPLAN_DR_Protocol>` — converges to a single final outline through arc Options≥2. analyzer→planner→[planner architect responsibility]→inspector **sequentially**. Split into `plan.md` (decision process) + outline (decision result).

**`--consensus` auto-trigger (Deliberate trigger)**: if any of defense · review committee · external official presentation applies, even when invoked with `--direct`, propose "consensus recommended — proceed?" to the user once (not auto-forced, overridable).
</Modes>

<Gate>
**Gate 1 — Structure lock.** Present the narrative arc + full outline to the user. No artifact exists yet —
this is where rearranging is cheapest. After approval, build. (For `--consensus`, present both plan.md + outline.)
</Gate>

<Steps>
### `--direct` path (default)
1. Dispatch doc-planner (pass the analyzer inventory + tone preset):
   `Task(subagent_type="oh-my-docs:doc-planner", ...)`
2. The planner produces the arc selection + a per-slide outline of purpose, message, and assets.
3. Confirm that all required sections are placed and that the format density limit (references/formats/<format>.md) is respected.
4. Present the outline as Gate 1 → approval.

### `--consensus` path (sequential — never parallel)
> ⚠️ The following MUST be sequential (stated three ways):
> ① (step-level) Each step issues the next Task only after awaiting the previous step's Task result. Do not call two Tasks in the same parallel batch.
> ② (Important) analyzer → planner → [planner architect responsibility] → inspector MUST be sequential. Await each stage's result.
> ③ (CRITICAL) Sequencing is guaranteed only by the controller's await (no runtime lock). Concurrent dispatch amplifies arc inconsistency.
1c. **analyzer** dispatch (when the inventory needs reinforcement; reuse the existing one if sufficient). Next step *only after* it finishes.
2c. **planner** dispatch (`--consensus` directive): triggers `<Consensus_RALPLAN_DR_Protocol>` — Principles + Drivers + arc Options≥2 + steelman + tradeoff + ADR + (if Deliberate) pre-mortem. Output = `plan.md` + outline.
3c. **[planner architect responsibility]**: not a separate agent — the planner already performs this via steelman/antithesis (T1: doc-architect is not newly created).
4c. **inspector** dispatch (`doc-inspector`): formative critique of plan.md + outline (4 critic techniques, severity). Does not issue PASS/FAIL.
5c. **re-review loop**: if the inspector raises critical/important, re-delegate to the planner (back to 2c), then re-critique. Max 5 rounds. On reaching 5, present the best plus "consensus not reached — remaining findings."
6c. **two-way split save**: `plan.md` (RALPLAN-DR+ADR) + outline (Final single arc). Present both as Gate 1.
</Steps>

<Output>
Narrative arc + per-slide/section {purpose, key message, required assets} outline. The blueprint docs-build will fill in.
**For `--consensus`, additionally**: `plan.md` (decision process — RALPLAN-DR+ADR) + re-review round (N/5) + whether consensus was reached. plan.md and the outline are two separate files (decision process ≠ decision result).
</Output>

<Consensus_Handoff>
> Handoff convention between `--consensus` sequential stages (isomorphic to scholar-outline). **Default (SSOT) = .md files**, MCP is an *optional accelerator when present* (decision 1=C: OMD's identity is 0 MCP / standalone).

**Default path (.md — works without MCP)**:
- Write each consensus stage's *structured output* (the planner's steelman/antithesis/tradeoff/ADR, the inspector's findings, etc.) to the workspace at `.omd/<slug>/consensus/<stage>-<role>.md`. e.g. `consensus/planner-adr.md`, `consensus/inspector-findings.md`. Structured header (role / stage / timestamp) + body.
- **rubber-stamp prevention (mechanical)**: the next stage proceeds only after *confirming the previous role's .md file exists on disk*. If absent, refuse to proceed. Directory isolation = namespace substitute. consensus is sequential, so no race.
- `<slug>` / paths are **relative to the work root** — no user-specific absolute paths.

**Optional (accelerator) MCP**: when config gate `agents.sharedMemory.enabled` + the shared_memory MCP are available, the same data may be mirrored via `shared_memory_write(namespace="doc-consensus", key="<stage>-<role>", value={...})`. ⚠️ **.md is the SSOT, MCP is the accelerator** — on absence, gracefully degrade to .md; not an error.

**Mixed-use clarity**: non-structured outputs such as the analyzer inventory stay as-is. The consensus/ directory is the workspace — subject to T18 cleanup on completion.
</Consensus_Handoff>
