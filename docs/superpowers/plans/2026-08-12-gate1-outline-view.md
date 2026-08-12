# Execution plan — GATE 1 outline view (omd v0.7.0)

Spec: `docs/superpowers/specs/2026-08-12-gate1-outline-view-design.md` (approved 2026-08-12,
including both §6 decisions). Branch `feat/gate1-outline-view`, already created.

**Method**: `superpowers:subagent-driven-development` — a fresh implementer per task, then a
spec-compliance review **and** a code-quality review before the next task starts. Model: `sonnet`
for every implementer and per-task reviewer (the plan is firm and the discretion is mechanical);
`opus` only for the final whole-branch review.

**Standing rules for every task**

- Tests first. A task is not done until its own tests fail for the right reason, then pass.
- Stdlib only. No new dependency, no network, no MCP.
- The renderer detects **absence, never quality** (spec §4). A reviewer who sees a flag that needs
  reading-for-sense must reject the task.
- Never write outside the repo. Never run `tokensave` CLI. No emoji in any file this plan touches.
- Do not bump the version, touch `CHANGELOG.md`, push, or open a PR until Task 7.

---

## The fixture, pinned once

Every test in Tasks 1–3 builds on this single healthy outline. It must trip **zero** flags. Copy it
verbatim into `tests/test_omd_outline_view.py` as a module-level `COMPLETE` string; each defect test
is `COMPLETE` with exactly one mutation.

```markdown
## Narrative Arc
**Arc/Frame**: defense (question - contribution - method - experiment - conclusion) — **Why**: a committee judges novelty first, then rigor.

## Outline
| # | Slide/Section | Purpose | Key message | Required asset |
|---|---------------|---------|-------------|----------------|
| 1 | Title | frame the talk | who, what, and when | none |
| 2 | Research question | establish the gap | localization fails under drift | figure |
| 3 | Contribution | state what is new | we add an adaptive filter | none |
| 4 | Method | show it is sound | the filter works by re-weighting | figure |
| 5 | Experiment | show it holds | it beats the baseline on the metric | table |

## Coverage Check
- Required sections all placed: yes
- Density limits respected: yes

## Open Questions (if any block the structure)
- none
```

Two vocabularies, both explicit and both tested — no other value is special-cased anywhere:

- **`EMPTY_TOKENS`** (a cell counts as missing): `""`, `"…"`, `"..."`, `"TBD"`, `"TODO"`, `"-"`.
  Case-insensitive, after strip.
- **`NO_QUESTION_TOKENS`** (an Open Questions item is not a question): `""`, `"…"`, `"..."`,
  `"none"`, `"n/a"`, `"na"`, `"-"`. Case-insensitive, after stripping a leading `-` and whitespace.

`"none"` is in the second list but **not** the first: an Open Questions item reading "none" is the
good outcome, while a cell reading "none" in the `Required asset` column is a real, intended value
(a title slide needs no asset). Getting these two backwards is the single most likely defect in
this feature — Task 2 must test both directions.

---

## Task 1 — `parse_outline`

**Create** `scripts/omd_outline_view.py` and `tests/test_omd_outline_view.py`.

Loader idiom for the test file — **load-bearing**, do not simplify:

```python
_spec = importlib.util.spec_from_file_location("omd_outline_view", SCRIPT)
ov = importlib.util.module_from_spec(_spec)
sys.modules["omd_outline_view"] = ov   # required before exec: @dataclass under PEP 563
                                       # resolves annotations via sys.modules[cls.__module__]
_spec.loader.exec_module(ov)
```

Omitting the registration line raises `AttributeError` at import time as soon as the module defines
a dataclass with `from __future__ import annotations`. `tests/test_snippets_*.py` get away without
it only because those modules define no dataclasses.

**Signature**: `parse_outline(text: str) -> Outline` — pure, no I/O, never raises on malformed
input. Anything it cannot understand becomes an absence for `flags()` to report, never an exception.

Dataclasses: `Unit(number: int | None, name: str, purpose: str, message: str, asset: str)`,
`Outline(arc: str, arc_why: str, units: list[Unit], coverage_sections: str | None,
coverage_density: str | None, has_coverage_check: bool, questions: list[str])`.

**Tests (RED first)**

1. `COMPLETE` parses to 5 units in table order; unit 1 is `Title`, unit 5 asset is `table`.
2. `arc` is the frame name and `arc_why` is the text after `**Why**:` — the two are split, and
   neither contains the other's marker text.
3. The header separator row (`|---|---|`) is not parsed as a unit.
4. A row with a trailing `|` and a row without one both parse identically (markdown allows both).
5. A missing `## Outline` section yields `units == []` and does not raise.
6. Text with no `**Arc/Frame**:` line yields `arc == ""` and does not raise.
7. A non-numeric `#` cell yields `number is None` and does not raise.
8. `has_coverage_check` is False when the `## Coverage Check` heading is absent; the two coverage
   fields are then `None`, distinct from the empty string.
9. Multi-digit and dotted unit numbers survive: an outline numbered 1..12 parses `[1..12]`, and a
   `#` cell of `4.5` does not silently become `4`. Assert the parsed numbers directly, not a count.

Test 9 is not hypothetical: the oms counterpart shipped a regression where a lazy number group
turned `10` into `1`, and it was invisible to every test that used single digits.

**Acceptance**: all 9 pass; `parse_outline` contains no `raise`; the module imports on a machine
with no third-party packages installed.

---

## Task 2 — `flags`

**Signature**: `flags(outline: Outline) -> list[Flag]`, `Flag(code: str, detail: str)`. Pure.
Nine codes, exactly as spec §3.4. Order the returned list by first occurrence; do not sort by code.

**Tests** — one per flag, each `COMPLETE` plus one mutation, asserting the **exact** set of codes
(`{"missing-field"}`, never `"missing-field" in codes`). A helper `codes(text)` returning the sorted
set keeps them one line each.

| Mutation | Expected set |
|:---|:---|
| unchanged `COMPLETE` | `set()` |
| unit 3's Purpose cell emptied | `{"missing-field"}` |
| unit 3's Purpose cell set to `TBD` | `{"missing-field"}` |
| unit 1's asset cell set to `none` | `set()` — legitimate value, guards the vocabulary mix-up |
| the whole Outline table removed | `{"no-units"}` |
| the `**Arc/Frame**:` line removed | `{"missing-arc"}` |
| `**Why**:` half emptied, frame name kept | `{"missing-arc"}` |
| unit numbers `1,2,4,5,6` | `{"number-gap"}` |
| unit numbers `1,2,2,3,4` | `{"number-gap"}` |
| unit 5 renamed to `Method` | `{"duplicate-unit"}` |
| `## Coverage Check` section removed | `{"no-coverage-check"}` |
| sections line reads `no — Related Work missing` | `{"coverage-unresolved"}` |
| density line reads `flag: slide 4 title 62 chars` | `{"density-unresolved"}` |
| an Open Questions item `- which dataset ships?` | `{"open-questions"}` |
| Open Questions section removed entirely | `set()` |
| Open Questions item `- n/a` | `set()` |

Plus two whole-outline tests: an outline that trips five different flags returns all five, and
`flags()` never returns a code outside the nine.

**`detail` requirements** — a reviewer must reject a flag whose detail cannot locate the problem:

- `missing-field` names the unit number and the column.
- `duplicate-unit` names the repeated name and both positions.
- `number-gap` prints the sequence it actually saw.
- `coverage-unresolved` / `density-unresolved` carry the planner's line **verbatim**, unedited.

**Acceptance**: every row above passes; no flag reads any cell for meaning.

---

## Task 3 — `render_html` + `main`

**`render_html(outline, defects) -> str`** — one self-contained page, no external fetch.

- A **panel strip**: numbered panels in reading order (CSS grid, `repeat(auto-fill, minmax(…))`),
  each carrying `#`, unit name, purpose, key message, and an asset chip. The arc name and its
  `Why` sit above the strip as the frame.
- Panels with a flag are marked visually **and** in text (never colour alone).
- The gaps list is rendered on the page with the same `detail` strings the CLI prints.
- Every flag with a `detail` must appear in the HTML — including `no-units`, whose panel strip is
  empty and whose detail is therefore the only thing on the page. (The oms counterpart shipped a
  bug where exactly this one rendered nothing.)
- Theme: define the full light palette on bare `:root`; redefine only tokens under
  `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }` and again under
  `:root[data-theme="dark"]`. `body` gets an explicit token background.
- HTML-escape every value from the outline. A `<` in a key message must not break the page.

**`main(argv=None) -> int`**

- `main(["outline.md", "-o", "gate1.html"])`; `-o` defaults to `gate1.html` beside the input.
- Writes the sheet **unconditionally before** the exit-code branch.
- Prints one line per gap, then `GAPS=<n>` as the last line.
- Returns `1` if any flag fired, else `0`.
- A missing input file goes through `parser.error` — the only raising path in the feature.

**Tests**: `render_html` output contains every unit name and every flag detail; `<script>` in a cell
appears escaped and not as a live tag; all three theme selectors are present; `main` on a healthy
outline returns 0 and prints `GAPS=0`; `main` on a defective one returns 1, still writes the file,
and prints one line per gap; `main` writes the file even when every flag fires. Use `tmp_path` and
`capsys`; never write into the repo tree.

**Acceptance**: the above pass; opening the written file in a browser shows a readable strip (the
implementer states this was actually done, or says it was not).

---

## Task 4 — the path SSOT

**Edit** `references/output-layout.md` §2, adding to the `.omd/<slug>/` block, with the existing
column alignment preserved:

```
  outline.md                          # approved structure (arc + outline + coverage check)
  plan.md                             # --consensus only: decision process (RALPLAN-DR + ADR)
  gate1.html                          # rendered view of outline.md
  consensus/
    <stage>-<role>.md                 # --consensus only: sequential handoff files
```

Also: §2.1's "four subdirectories" sentence is already inaccurate (the block lists more than four).
Reword it to state the invariant it actually means — these names are fixed, and a new intermediate
maps into an existing one rather than inventing a sibling — without changing that rule.

Add to §6's implementation checklist: `docs-plan` writes `outline.md` before Gate 1.

**Do not** add `outline.md` or `plan.md` to the §5.2 cleanup table. State why in one line: they are
the specification the artifact was built from, and revise/rebuild needs them after renders are gone.

**Tests** — append to `tests/test_output_layout_contract.py`, matching its existing assert-on-card
style: the card names `outline.md`, `plan.md`, `gate1.html`, and `consensus/`; the cleanup table
(§5.2) does not name `outline.md`.

**Acceptance**: new tests pass, all pre-existing tests in that file still pass unchanged.

---

## Task 5 — wire `docs-plan` Gate 1

**Edit** `skills/docs-plan/SKILL.md` only (never a shim — omd has none; `skills/` is authoritative
here, unlike oms).

`--direct` step 4 and `--consensus` step 6c both become: save → render → report → present.
`<Gate>` gains one sentence pointing at the rendered sheet. Required content, in order:

1. Save the planner's returned block to `.omd/<slug>/outline.md` (`--consensus`: `plan.md` too).
   The **controller** writes; `doc-planner` stays read-only.
2. Render `python3 scripts/omd_outline_view.py .omd/<slug>/outline.md -o .omd/<slug>/gate1.html`,
   and surface it opportunistically — artifact where the harness has one, otherwise the file path.
   Absence of a viewer is a graceful degrade, never an error.
3. Report the gaps verbatim, including this sentence, which must appear in the skill body word for
   word:

   > `GAPS=0` means nothing mechanical is missing — it is **not** a judgment that the structure is
   > good, and must never be presented as one.

**Tests** — new `tests/test_gate1_outline_view_wiring.py`: `docs-plan/SKILL.md` names
`omd_outline_view.py`, `outline.md`, and carries the `GAPS=0` sentence verbatim;
`agents/doc-planner.md` frontmatter still contains `disallowedTools: Write`.

**Budget guard**: `tests/test_skill_budget.py` caps `skills/*/SKILL.md` at 100 KiB total; the
current sum is 69,594 B, so there is room — but run that test and report the new total.

**Acceptance**: new tests pass; skill-lint and skill-contract tests still pass.

---

## Task 6 — the six downstream edit points

Spec §6 decision 2, phrasing only, no logic:

| File | Line | Change |
|:---|:--|:---|
| `agents/doc-builder.md` | 41 | "Read the approved outline" names `.omd/<slug>/outline.md` |
| `agents/doc-builder.md` | 59 | the compared slide count comes from that file |
| `agents/doc-verifier.md` | 46 | "Read the approved outline" names the path |
| `skills/docs-verify/SKILL.md` | 38 | "passing the outline" names the path |
| `skills/docs-build/SKILL.md` | 45 | "pass the outline" names the path |
| `skills/docs-revise/SKILL.md` | 31 | completeness is checked against that file |

Line numbers are from 2026-08-12 and are a starting point, not an address — locate the sentence,
not the line. `references/snippets/assert_shapes.py` gets **no change**; it already takes
`outline_slide_count` as a parameter.

**Tests** — extend `tests/test_gate1_outline_view_wiring.py`: each of the five files names
`.omd/<slug>/outline.md`. Assert on the path string, not on surrounding prose.

**Acceptance**: new tests pass; `test_skill_contract.py`, `test_skill_lint.py`,
`test_agent_contract.py` all still pass (they scan exactly these files).

---

## Task 7 — release

1. `.claude-plugin/plugin.json` → `0.7.0`.
2. `CHANGELOG.md`: a `## [0.7.0] - 2026-08-12` section under an untouched `## [Unreleased]`,
   in this repo's existing Korean prose style. **Added**: outline persistence at
   `.omd/<slug>/outline.md`, the Gate 1 rendered view, the nine absence flags. **Changed**: the
   path SSOT gains outline/plan/consensus/gate1 entries; six downstream roles now name the path.
   State plainly that the renderer detects absence and never judges quality.
3. `README.md`: only if it already enumerates stages or scripts — check, then say which it was.
4. Run `python3 scripts/sync_version.py` and report all four surfaces. The omha card is expected to
   remain drifted (`0.6.1`, five releases stale, a separate repo) — report it, do not fix it.
5. Run the **full** suite and paste the exact counts.
6. Do **not** push and do **not** draft a PR body. Stop and report.

**Acceptance**: full suite green, four version surfaces reported honestly, nothing pushed.

---

## Final review (after Task 7)

One whole-branch review at `opus`, adversarial, against the spec. It must actually execute the
renderer on at least one mutant outline rather than reading the diff — the oms counterpart's two
most serious defects were both found by running mutants and both invisible to reading. Findings are
fixed in **one** wave; a fix that changes a regex or a parse rule gets a scoped re-review before
merge, because the oms fix wave introduced a critical regression that its own new tests did not
catch.
