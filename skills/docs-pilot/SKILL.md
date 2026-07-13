---
name: docs-pilot
description: |
  One-line brief → orchestration of an entire finished document. Weaves the
  intake→standardize→plan→build→inspect→verify stages together, confirming with the user at every gate.
  The document-side counterpart of OMC autopilot. A self-sufficient entry point —
  an upstream meta-harness can invoke it with a single line: "delegate to OMD."
  Triggers: 통째로 만들어줘, 처음부터 끝까지, 발표자료 다 만들어, 이 PDF로 디펜스 자료,
  docs pilot, document autopilot, 문서 자동, end to end 문서, 알아서 만들어
---

# docs-pilot — production orchestrator

<Purpose>
Automatically orchestrates every stage from brief to finished document (intent crystallization → standard extraction → design → production → inspection → verification). The user only states *what is needed*; the harness decides *which tools, what structure, and how to verify*. However, because the risk (a full rework) is large, it confirms at every gate — not fully autonomous.
</Purpose>

<Use_When>
- End-to-end requests like "make the entire defense material out of this PDF"
- When an upstream meta-harness (omha) delegates document work to OMD (self-sufficient entry point)
</Use_When>

<Do_Not_Use_When>
- When only one stage is needed → call that stage's skill directly (docs-inspect only, docs-build only, etc.)
- citation-bound documents (papers, etc.) → no parallelization; the builder handles it alone and carefully (hallucination risk)
</Do_Not_Use_When>

<Execution_Policy>
- Each stage is dispatched as a fresh subagent — protecting the controller context.
- Proceed to the next stage only after user confirmation at gates 0~3. The risk = full rework, so confirmation is never skipped.
- inspect (formative) and verify (summative) are in a different lane from the builder — no self-approval.
- On FAIL, fall back to docs-build for the fix loop (up to a reasonable number of iterations; if the same defect recurs 3 times, stop and report).
- Skip any stage whose spec is already satisfied (see the skip conditions under Steps below).
- **Record priority context on entry (survives compaction)**: at the start of the pipeline, write the critical constraints into the `## Priority Context` section of `.omd/notepad.md` — "no in-place modification of the original / the final is a single `outputs/<slug>/current.<ext>`, versions and intermediates go to `.omd/<slug>/` / current gate n + slug". So that even if the context is compacted during a long pipeline, original-destruction prevention and gate position are always recoverable.
  - **.md is the default**: write/append directly to `.omd/notepad.md`. If the notepad MCP is available, you may mirror it via `notepad_write_priority(...)` (same .md target, optional acceleration) — without it, the same behavior is achieved by writing the .md, not an error. Contract (3 tiers, pruning, compaction-survival): `references/notepad.md`.
- The workspace path is fixed at **`.omd/<slug>/`** (a verified real path; do not bolt on unverified sub-segments like `.omd/specs` or `sessions/{sid}`).
  - ⚠️ **30s trap (only relevant if a state MCP is introduced later — not applied now)**: if you start using a state MCP, do not call `state_clear` *right before* a stage handoff (for 30s it disables the stop-hooks of all modes, silently breaking the loop). Use `state_write(active=false)` for non-terminal handoffs, and `state_clear` *only at the terminal (full pipeline shutdown)*. **Currently no state MCP is actually called (.md/`.omd/` files are the default), so this is a purely forward-looking note.**
- **Stage-evidence markers (G5)**: at every stage 1–6 decision, append exactly one line to
  `.omd/<slug>/stage-evidence.log` — `OMD stage <n> <name> → spawned oh-my-docs:doc-<agent>`
  when dispatching, or `OMD stage <n> <name> → skipped: <reason>` when the skip condition
  holds. The Stop guard greps this log and flags stages with neither marker (advisory) —
  the delegation-evidence trail is how "the pilot quietly did a stage inline" gets caught.
</Execution_Policy>

<Steps>
1. **docs-intake** → dispatch doc-analyzer: intent crystallization + input inventory + Round 0 topology + 4-dimension qualitative ambiguity judgment (Audience/Message/Evidence-density/Constraint).
   - *If the spec is already clear (format, audience, tone all set) and all 4 dimensions are clear*, skip.   ──[Gate 0: intent]
2. **docs-standardize** → dispatch doc-analyzer: if reference documents exist, extract the common standard.
   - *If no reference documents exist*, skip (use the default tone preset).
   - **⚠️ Mandatory exception — NON-SKIPPABLE when a template/sample is supplied**: if the user provides a master template (a .pptx etc. with real layouts) or a sample to follow, standardize is **required**. What you extract here is not a tone preset but the **layout/placeholder map the builder will clone** (layout index, placeholder idx/type, inherited font and number style) — `references/formats/pptx.md` "Building on a master template" presupposes this map. Going straight to build without it makes the builder hand-draw on blank slides and ignore the template wholesale (the entry point of the 2026-06-16 v1–v3 regression). The "no reference document" skip is valid only for free-form documents, not for the template-supplied case.
3. **docs-plan** → dispatch doc-planner: narrative arc + outline.
   - **Mode branch**: if a Deliberate trigger (defense / review / external official presentation), use `docs-plan --consensus` (RALPLAN-DR 4-agent sequential); otherwise `--direct`. Automatic judgment + user override.  ──[Gate 1: structure. If consensus, present both plan.md + outline]
4. **docs-build** → dispatch doc-builder: read the cards and produce via the engine (including equations). ──[Gate 2: content]
5. **docs-inspect** → dispatch doc-inspector: PPTEval 3-axis formative critique.
   - Parallel with the build fix loop (spec≠quality separation).
6. **docs-verify** → dispatch doc-verifier: integrity 5/5 + full read-through.       ──[Gate 3: final]
   - FAIL → fall back to step 4 (build).
7. **wiki capture (automatic specialization — the more you use it, the more it adapts to this project / this presentation type)**: the reusable patterns that inspect/verify *discovered* in this session are **automatically appended** to the **target project's `.omd/wiki/<category>/*.md`** (the project workspace, not the plugin; `.omd/` is gitignored) (no approval needed — lightweight channel). This is the data that the next session's doc-inspector pre-commitment `wiki_query(category)` reads — writing and reading close the loop, so the more you use the harness the more it specializes to this presentation type and this organization's standard. (Being a workspace, it doesn't pollute the plugin distribution or other projects, and it isn't blown away by a marketplace update.)
   - **What to load**: ① recurring defect patterns per presentation type → `convention/<type>-defect-patterns.md` (e.g., defense = blurry contributions, missing ablation) ② the common format induced by standardize (font, color, margins) → `convention/<org>-style-spec.md` ③ the rationale for the arc and audience framing chosen this time → `decision/<slug>.md`. Only what the inspector/verifier and standardize actually observed — no loading of speculation.
   - **Append format**: add one line (or a short entry) to the end of the existing .md. If the same pattern already exists, do not duplicate it (grep first to check). A new category file is free-form .md (no machine schema).
     New category-file names come from `query_helper.title_to_slug()` (English-keyword slug —
     it owns the deterministic hash fallback, KN-4), and the target path is validated with
     `query_helper.safe_wiki_path()` before any Write into `.omd/wiki/**` (KN-3). python3
     unavailable → follow the README naming rule by hand and stay strictly inside
     `.omd/wiki/<category>/`.
   - **Automatic but non-destructive**: append-only (never erases existing lines), creates absent directories, and just passes through if there's nothing to load (an empty session is OK). Both loading and querying use **deterministic text only, no embeddings**. If the user passes `--no-wiki`, skip. For the contract and boundaries, see `references/wiki/README.md`.
   - **⚠️ 2 tiers — append goes local only, global gets a hint only**: automatic append always writes only to the **local** `.omd/wiki/` (this project) (lightweight channel). Queries (`wiki_query`) merge and read local + the parent `.omd/wiki/` (global, ascent). **Global promotion candidate hint (terminal only)**: at pipeline shutdown, if among what accumulated locally this time there are assets *reusable for the next document* (tendencies, organization/type formats, reusable decisions), **suggest** to the user: "Shall I promote this to the parent `.omd/` (global)?" — the actual promotion is performed by `docs-learn`'s local→global path (§4b, human gate), and that step enforces ⚠️ **content 0 (document text, figures, and claims are permanently forbidden globally) + project-identifier scrub (식별자 스크럽)** (remove customer names, internal codenames, confidential paths; keep only abstract form rules — "caption 12pt black" is OK, "ACME deck has red captions" stays local). pilot only suggests — no automatic promotion. Rationale: `skills/docs-learn/SKILL.md` §4b, `references/learning-protocol.md` §1.4·§6.F (cross-project confidentiality isolation).
8. **terminal cleanup** (after verify PASS + the user's final confirmation at gate 3, or when the user explicitly says "clean up" / "work done"):
   - **Aggregate** the cleanup targets in `.omd/<slug>/` (size, count): all of `renders/`·`gen-image/`·`tmp/` + old versions in `versions/` **excluding** the latest one and any user-specified milestones. To choose milestones, show the user the versions list.
   - **AskUserQuestion [clean up / keep]** — never auto-delete, default conservative (keep).
   - On "clean up" → **delete via a recoverable path** (no permanent `rm`): macOS `trash` (if absent, move to `~/.Trash`) / Linux `gio trash`·`trash-cli` / Windows PowerShell move-to-recycle-bin (`Shell.Application` ParseName+InvokeVerb('delete'), no permanent `Remove-Item` — documented, unverified) / in environments without a recycle bin (CI, containers) only after user re-confirmation of "permanent deletion".
   - ⚠️ `outputs/<slug>/current.<ext>` (the user's asset) is **excluded** from aggregation and deletion — only mentioned. For the detailed procedure, see `references/output-layout.md` §5.

> **`--from <stage>` entry point**: you can start from an intermediate stage — `intake|standardize|plan|build|inspect|verify`. intake's topology/ambiguity judgment is included in `--from intake`.
</Steps>

<Output>
What the user sees as the final is `outputs/<slug>/current.<ext>` (the single one that received PASS) + an optional verify evidence table.
Version history, renders, and intermediates go to the workspace `.omd/<slug>/` (`versions/`·`renders/`·`gen-image/`·`tmp/`) — the path convention's SSOT is `references/output-layout.md`. Each stage's output connects as the next stage's input.
</Output>

<Self_Sufficiency>
This skill is a self-sufficient entry point. So that an upstream meta-harness (omha) can invoke document work with a single line "delegate to OMD docs-pilot", it completes all stages from the brief alone, without external context.
</Self_Sufficiency>
