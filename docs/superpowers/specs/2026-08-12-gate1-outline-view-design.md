# Design — GATE 1 outline view (omd)

> Status: draft for approval · 2026-08-12 · target release **v0.7.0**
> Counterpart: `oh-my-scholar` v0.14.0 shipped the isomorphic feature for the paper lane
> (`docs/2026-08-12-gate1-outline-view-design.md` in that repo). That spec's §10 deferred omd
> to its own spec **because omd's outline is not persisted at all** — this document closes that.

## 1. The problem

`docs-plan` (stage 3) ends at a human gate:

> **Gate 1 — Structure lock.** Present the structure frame + full outline to the user. No artifact
> exists yet — this is where rearranging is cheapest. After approval, build.
> — `skills/docs-plan/SKILL.md:33-36`

Two defects sit behind that gate, and the second is the load-bearing one.

**(a) The outline is presented, never rendered.** It reaches the user as whatever prose the
controller chooses to paste into the turn. The user approves a structure they read in a scrollback.

**(b) The outline has no path.** This is not a cosmetic gap:

| Consumer | What it is told to read | Where |
|:---|:---|:---|
| `doc-builder` | "produce the artifact **from an approved outline**" | `agents/doc-builder.md:3,10` |
| `doc-verifier` | "Read **the approved outline** (for spec completeness)" | `agents/doc-verifier.md:46,50` |
| `docs-verify` | "Dispatch doc-verifier (passing **the outline** + output path)" | `skills/docs-verify/SKILL.md:38` |
| `docs-revise` | "All required **outline** sections present" | `skills/docs-revise/SKILL.md:31` |
| `references/snippets/assert_shapes.py:63` | compares slide count against `outline_slide_count` | already coded |

Five consumers name the outline as an input. **`references/output-layout.md` — the SSOT that exists
to give the single fixed answer to "where does each file go" — has no outline entry.** In `--direct`
mode (the default) the outline is conversational only; in `--consensus` mode the skill promises a
"two-way split save: `plan.md` + outline" (`docs-plan/SKILL.md:56`) and names a path for neither.

So the artifact the whole downstream pipeline is defined against exists only in a context window.
That is the same failure class the `--consensus` handoff already guards *between agents* — it
refuses to advance a stage without the previous role's `.md` on disk (`docs-plan/SKILL.md:69`) —
left open on the axis where it matters most: the human gate, and every stage after it.

## 2. What this is not

- **Not a quality judgment.** The renderer detects *absence*, never quality. See §4; this is the
  single most important constraint in the document.
- **Not a new planner schema.** `doc-planner`'s `<Output_Format>` already fixes the shape
  (`agents/doc-planner.md:70-100`). We persist and parse what it already emits.
- **Not a change to the `--consensus` protocol.** Sequence, roles, round cap, and the plan/outline
  split are untouched. Only their paths get written down.
- **Not a new agent, not a new stage, not an MCP dependency.** omd's identity is 0 MCP / standalone
  (`docs-plan/SKILL.md:65`) and that holds here.
- **Not a gate that blocks.** The renderer never raises into the pipeline and never withholds the
  gate. It prints, writes, and exits.

## 3. Design

Two halves. The second is impossible without the first, which is why oms's spec deferred omd.

### 3.1 Persist — the outline gets a path

`references/output-layout.md` §2 gains three entries under `.omd/<slug>/`:

```
.omd/<slug>/
  outline.md                          # the approved structure (planner's Narrative Arc + Outline
                                      #   + Coverage Check). Written at Gate 1, before approval.
  plan.md                             # --consensus only: the decision *process* (RALPLAN-DR + ADR)
  consensus/                          # --consensus only: <stage>-<role>.md handoff files
  gate1.html                          # the rendered view of outline.md (§3.3)
```

Three notes on that block:

1. **`consensus/` is already written today** by `docs-plan --consensus` and is simply missing from
   the card. Adding it is a factual correction to the SSOT, not a new behaviour.
2. **The controller writes these, not the planner.** `doc-planner` is `disallowedTools: Write, Edit`
   (`agents/doc-planner.md:6`) and stays that way — the skill saves the agent's returned block.
3. **`outline.md` is written before the gate, not after approval.** A file the user has not yet
   approved is exactly what the gate is for; writing it after approval would leave `--direct` with
   nothing to render at the moment the render is needed.

`.omd/` is already gitignored and already cleaned at terminal (`output-layout.md` §5) — `outline.md`
inherits both. It is **not** added to the §5.2 cleanup table: it is the specification the artifact was
built from, and a rebuilt or revised document needs it after the renders are gone.

### 3.2 The format is the planner's existing output contract

No schema is invented. `outline.md` is the planner's block verbatim:

```markdown
## Narrative Arc
**Arc/Frame**: <name> — **Why**: <one line>

## Outline
| # | Slide/Section | Purpose | Key message | Required asset |
|---|---------------|---------|-------------|----------------|
| 1 | …             | …       | …           | figure/table/none |

## Coverage Check
- Required sections all placed: yes
- Density limits respected: yes

## Open Questions (if any block the structure)
- …
```

It is a markdown table, so parsing is a split on `|` — no dependency, no format negotiation, and the
parser stays correct for free whenever the planner is faithful to its own contract. The same block
serves all three genres (office / repo-docs / site); only the *values* differ, which is why the
renderer is genre-blind.

### 3.3 Render — `scripts/omd_outline_view.py`

Stdlib only, no deps, same shape as the oms counterpart:

```python
parse_outline(text: str) -> Outline      # pure, no I/O
flags(outline: Outline) -> list[Flag]    # pure
render_html(outline: Outline, defects: list[Flag]) -> str
main(argv: list[str] | None = None) -> int
```

CLI: `python3 scripts/omd_outline_view.py .omd/<slug>/outline.md -o .omd/<slug>/gate1.html`

- Writes the sheet **unconditionally, before** the exit-code branch — a defective outline is exactly
  when the user most needs to see it.
- Prints one line per gap, then `GAPS=<n>`.
- Returns `1` if any flag fired, else `0`. A missing input file is a `parser.error` — **the only
  raising path in the feature**.
- Output is a self-contained HTML page: no external fetch, all three theme states defined at token
  level (bare `:root`, `prefers-color-scheme: dark` guarded with `:root:not([data-theme="light"])`,
  and `:root[data-theme="dark"]`).

**Visual form: a panel strip, not a table.** This is the one place the omd renderer deliberately
diverges from the oms one. An omd outline *is* a sequence of slides or sections, so it renders as
numbered storyboard panels in reading order — each panel carrying `#`, the unit name, purpose, key
message, and an asset chip. The arc and its justification sit above the strip as the frame. That is
the literal storyboard the feature is named after, and the sequence is the thing the user is being
asked to approve.

### 3.4 Flags — ten, all absence

| # | Code | Fires when |
|:--|:---|:---|
| 1 | `no-units` | the Outline table has zero data rows |
| 2 | `missing-field` | a row has an empty or placeholder cell (name / purpose / key message / asset) |
| 3 | `missing-arc` | `**Arc/Frame**:` absent, or its name or its `**Why**:` half is empty |
| 4 | `number-gap` | the `#` column is not contiguous ascending `1..N` (a skip or a repeat) |
| 5 | `duplicate-unit` | two rows carry an identical Slide/Section name |
| 6 | `no-coverage-check` | the `## Coverage Check` section is absent entirely |
| 7 | `coverage-unresolved` | "Required sections all placed" is not `yes` — reported **verbatim** |
| 8 | `density-unresolved` | "Density limits respected" is not `yes` — reported **verbatim** |
| 9 | `open-questions` | the Open Questions section is non-empty |
| 10 | `malformed-row` | an Outline row did not split into exactly 5 cells |

Documented exemptions — each is a case where absence is *correct* and must not flag:

- **An absent or template-only Open Questions section is normal.** The planner's contract says
  "if any block the structure"; nothing blocking is the good outcome. Only a non-empty list flags.
- **`Required asset: none` is a legitimate value**, never `missing-field`. A title slide needs no figure.
- **`plan.md` is never parsed.** The renderer reads the outline and nothing else, so `--direct` and
  `--consensus` produce the same sheet from the same input.

**`malformed-row` was added after the initial 9, during the final review wave (2026-08-12), and this
is the record of why.** An unescaped `|` inside a table cell (e.g. a title containing a literal pipe)
shifts every column right of it by one, and none of the other nine codes catches that: `missing-field`
stays silent whenever all the shifted cells happen to be non-empty, which is the common case. Still pure
character-presence (a cell count, never a read for sense) — it belongs to the same invariant as the
other nine, just late to the table.

**Deliberately not implemented: a slide-count or density budget flag.** oms has `over-budget`
because its outline carries a machine-readable `page_limit` and per-section word counts. omd's
density limits live in `references/rubrics/ppteval.md:14` as a *rubric axis for human/agent
judgment* ("KO title ≤ 50 chars, body ≤ 6 words/line"), and no per-outline number exists to check
against. Inventing one would require extending the planner contract, and checking prose against a
rubric is judgment — which §4 forbids. The planner's own self-report is what flags 7 and 8 surface.

### 3.5 Wiring — `docs-plan` Gate 1

`<Gate>` and step 4 (`--direct`) / step 6c (`--consensus`) gain, in order:

1. Save the planner's block to `.omd/<slug>/outline.md` (and `plan.md` for `--consensus`).
2. Render `gate1.html` and surface it **opportunistically** — as an artifact where the harness
   supports one, otherwise as a file path. Absence of a viewer is a graceful degrade, never an error.
3. Report the gaps **verbatim**, including this sentence, which is not optional:

   > `GAPS=0` means nothing mechanical is missing — it is **not** a judgment that the structure is
   > good, and must never be presented as one.

Then the existing present-and-approve behaviour proceeds unchanged.

## 4. Why the renderer must never judge

A checker that scores an outline becomes a reviewer nobody reviews. The user then reads a green
verdict on a structure no human evaluated, and the gate — whose entire purpose is that a person
looks at the shape while changing it is still free — converts into an *accelerated* rubber stamp.
That is strictly worse than no renderer at all, because it manufactures confidence.

So the contract is: **the renderer proves that the planner filled in the boxes. It proves nothing
about whether the boxes are right.** Every flag in §3.4 is answerable by looking for a character
that is or is not there. None requires reading for sense. When a future change proposes a flag that
needs a model to evaluate content, that flag belongs to `doc-inspector` (formative critique) or
`doc-verifier` (summative gate) — both of which already exist for exactly this, and neither of which
is what a 40-line parser should become.

## 5. Tests

`tests/test_omd_outline_view.py`, house style: pytest, plain `assert`, stdlib only, loaded via
`importlib.util.spec_from_file_location` — **with the module registered in `sys.modules` before
`exec_module`**, which is load-bearing whenever the module defines a `@dataclass` under
`from __future__ import annotations` (this exact omission cost a task in the oms build).

Shape: one module-level `COMPLETE` fixture — a healthy outline that trips nothing — and every defect
test is `COMPLETE` with a single targeted mutation, asserting the **exact** flag-code set rather than
membership, so a fix that silently widens a flag fails the suite.

Plus contract tests in the existing style (`test_output_layout_contract.py` asserts on card strings):

- `output-layout.md` names `outline.md`, `plan.md`, `consensus/`, `gate1.html`
- `docs-plan/SKILL.md` carries the render step and the verbatim `GAPS=0` sentence
- `doc-planner.md` remains `disallowedTools: Write` (the controller writes, the planner does not)

Budget check: `skills/*/SKILL.md` totals 69,594 B against the 100 KiB cap
(`tests/test_skill_budget.py`) — 32 KiB of headroom, so the `docs-plan` addition is not at risk.

## 6. Decisions (settled 2026-08-12)

1. **`plan.md` and `consensus/` are in scope.** Both are added to the card alongside `outline.md`.
   `consensus/` in particular is a factual correction — `docs-plan --consensus` writes there today
   and the path SSOT does not say so.
2. **The downstream consumers are rewired in this release.** (This overrides the spec's original
   recommendation to defer; the deferral would have left five roles still pointing at "the approved
   outline" with no path, which is the defect this release exists to close.) Six edit points, all
   phrasing — no logic changes:

   | File | Line | Change |
   |:---|:--|:---|
   | `agents/doc-builder.md` | 41 | "Read the approved outline" names `.omd/<slug>/outline.md` |
   | `agents/doc-builder.md` | 59 | the slide count compared against comes from that file |
   | `agents/doc-verifier.md` | 46 | "Read the approved outline" names the path |
   | `skills/docs-verify/SKILL.md` | 38 | "passing the outline" names the path |
   | `skills/docs-build/SKILL.md` | 45 | "pass the outline" names the path |
   | `skills/docs-revise/SKILL.md` | 31 | completeness is checked against that file |

   `references/snippets/assert_shapes.py` needs **no code change**: it already accepts
   `outline_slide_count` as a parameter (line 63). What was missing was any statement of where that
   number comes from, and that is doc-builder step 6's sentence — covered by the row above.

## 7. Release

`v0.7.0` (minor — new user-visible capability, no breaking change). Version SSOT
`.claude-plugin/plugin.json`, checked across four surfaces by `scripts/sync_version.py`. Note that
the omha card surface is already drifting at `0.6.1` against `0.6.6` — five releases behind, so it
is evidently not maintained per-release and this release does not change that either way.
