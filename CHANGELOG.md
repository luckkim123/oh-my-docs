# Changelog

All notable changes to oh-my-docs (omd).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/). Version
SSOT: `.claude-plugin/plugin.json` `version`.

> **Policy note (2026-07-13, R1)**: the earlier deliberate **commit-SHA versioning** policy is
> superseded by the R1–R4 release train (spec: `docs/superpowers/specs/2026-07-11-omd-program-design.md` §5).
> Entries below predating v0.1.0 were written under the old policy and stay as-is;
> the git log remains the SSOT for pre-semver general content changes.
> **R2 (2026-07-13)**: pre-semver entries were consolidated verbatim under the "Historical" tail
> section below — superseding R1's keep-in-place note; content unchanged.

## [Unreleased]

## [0.3.0] - 2026-07-14

Site genre: MkDocs + Material static documentation sites join the harness as a card
(D1 — no new skill), with machine-measured engine stamps and omd's own docs site as
the E2E pilot.

### Added
- `references/formats/site.md` — site genre card: uvx-run MkDocs engine table (measured
  on this machine), Diátaxis structure frames, standard mkdocs.yml skeleton with a
  mandatory `validation:` block, 5-item deterministic verify gate, built-HTML placement
  rule (`.omd/<slug>/site-build/`, never inside `current/`).
- `references/rubrics/site-rubric.md` — 2 qualitative lenses (Information architecture /
  Prose quality); build & link integrity stays mechanical in the card gate (PS-3).
- E2E pilot: omd's own docs site built through the pipeline and pinned as
  `tests/fixtures/omd-site/` with a stdlib permanent guard (`tests/test_site_dogfood.py`).
- `mkdocs build` signals in `docs_verify_emit.py` with verify-first matching — a
  `--strict` run clears the verify sentinel instead of re-arming it.

### Changed
- Route checkpoint advertises `site` (R2 pin test inverted — advertising synced to card
  existence); format enumerations updated across route tests.
- Front pipeline (docs-intake, doc-analyzer) and docs-build carry the site genre frame;
  docs-build gate/steps/output generalized beyond PNG evidence (fresh-read for text genres).
- Carryover cosmetics: plugin description and README name the text genres; doc-planner
  checklist asks for "exactly one structure frame" instead of a narrative arc.

> **Verification**: python3 -m pytest tests/ -q — 136 passed ·
> site pilot gates measured green: `mkdocs build --strict` exit 0 + markdownlint-cli2 exit 0
> (logs under `.omd/omd-site/verify-runs/`, uncommitted by policy).

> **Notes**: MQ-2 (fenced-JSON verify output) re-rejected at R3 — no consumer emerged
> (docs-revise consumes the table; verify-runs/ carries machine evidence); user-ratified at
> merge. lychee remains optional/UNVERIFIED. CJK search trap stays a candidate (pilot is
> English). Engine stamps use ephemeral runners (uvx/npx) — no global installs.

## [0.2.0] - 2026-07-13

R2 "repo-docs genre" — first text genre lands via card-only extension (D1: new format =
new card, no new skill), consuming the §4.4 infrastructure generalization (spec §5 R2).

### Added
- **repo-docs genre card** `references/formats/repo-docs.md`: standard-readme /
  keep-a-changelog / community-health / CODEOWNERS knowledge, genre section presets
  (library·cli·dataset), intake set-scope gate, analyzer input whitelist (AC-3), and a
  7-item deterministic verify gate incl. the placeholder scan (PL-3) — external links
  stay an optional lychee item (network-dependent).
- **repo-docs rubric** `references/rubrics/repo-docs-rubric.md`: qualitative lenses only
  (welcoming / information scent / honesty — frame per Treude et al.); mechanical axes
  live in the card gate (PS-3 dynamic lens composition).
- **md-genre verify trigger (D5)**: `docs_verify_emit` now watches Edit|Write on
  `outputs/<slug>/**/*.md` (slug-context gated), arms the same verify-pending sentinel,
  and `markdownlint` runs clear it; plugin.json registers the Edit|Write matcher.
- **Artifact-set layout (D4)**: `outputs/<slug>/current/` directory deliverables with
  `.omd/<slug>/manifest.json` ({path, sha256, role}), directory-wise version snapshots
  (LC-1), `verify-runs/` engine-log capture (AC-1b), atomic manifest writes (ST-1).
- **skill-contract guard** `tests/test_skill_contract.py`: every concrete references/
  path named by skills/agents must exist (AC-4 — H7-class drift regression).
- **Dogfooding guard** `tests/test_repo_docs_dogfood.py`: omd's own README/CHANGELOG
  permanently held to the repo-docs mechanical gate.

### Changed
- **Pipeline generalized to card delegation (§4.4)**: intake/plan skills + planner/
  analyzer agents consume card-defined genre frames (F7 front-end unblock); builder/
  verifier pair + inspect/verify/standardize/revise skills delegate gates to the card
  (F3/F6/PS-1~5); engine-missing verdict standardized as `UNVERIFIED (engine
  unavailable)` (D3). Office contracts preserved verbatim as the office cards' case.
- Routing CHECKPOINT advertises `repo-docs` in the FORMAT slot; `site` deliberately
  deferred to R3 with a pinning test (card-existence rule).
- `references/themes/` declared office-only (F8); convert/translate explicitly reject
  artifact-set inputs (LC-3); learning-protocol D7 gains text-genre form/content
  boundary examples.
- **README/CHANGELOG regenerated through the new pipeline** (dogfooding acceptance):
  README now follows the library preset; pre-semver changelog history consolidated
  verbatim under a `## Historical` tail (supersedes R1's keep-in-place note).
- `plugin.json author` field documented as intentional attribution metadata — the one
  sanctioned identifier under the D8 scan (user-ratified via this PR).

> **Verification**: `python3 -m pytest tests/ -q` — 115 passed
> (R1 baseline 67). markdownlint-cli2 gate run on README/CHANGELOG — exit 0
> (markdownlint-cli2 v0.23.0), log under
> `.omd/omd-dogfood/verify-runs/` (uncommitted).
>
> **Notes**: MQ-2 (fenced-JSON verify output) deliberately NOT adopted this release —
> no machine consumer yet; revisit at R3 (plan decision 1). LOCAL ONLY: marketplace
> update + app restart required after merge (spec §7 ⑤).

## [0.1.0] - 2026-07-13

R1 "hygiene + core gates" — first semver release (release train: spec
`docs/superpowers/specs/2026-07-11-omd-program-design.md` §5).

### Added
- Version SSOT: `plugin.json` `version` field + `tests/test_version_sync.py` (H3).
- Distribution-axiom guard: `tests/test_distribution_axiom.py` — no personal home paths /
  emails in shipped files, pattern-based per spec DT-3 (D8).
- Skill context budget guard: `tests/test_skill_budget.py`, 100 KiB cap (IA-1).
- Format-card authoring contract `references/formats/README.md` — required sections,
  VERIFIED stamp grammar, **engine-drift demotion rule** (`UNVERIFIED (engine drift)`),
  enforced by `tests/test_format_cards.py`; builder/verifier now run an engine-version
  pin check (G7).
- Agent contract guard `tests/test_agent_contract.py`: frontmatter model policy +
  Final_Response_Contract markers + self-approval bans (AC-1a).
- **model-guard hook** `hooks/model_guard.py` (PreToolUse Task): advisory warning on
  explicit model overrides contradicting agent frontmatter, and on unknown
  `oh-my-docs:*` agent names (G4).
- **verify-pending handshake** (G1): `docs_verify_emit` arms `.omd/**/.verify-pending`
  on document builds and clears it on verify signals; new Stop hook
  `hooks/docs_stop_guard.py` lists still-pending documents at Stop — strictly advisory,
  re-entry-safe (`stop_hook_active`), stale sentinels marked "carried over", never blocks.
- Reminder cooldown: same-content verify reminders are throttled for 10 min
  (`.omd/.hook-throttle.json`, `OMD_REMINDER_COOLDOWN_SECONDS` override) (HG-3).

### Changed
- **Versioning policy**: commit-SHA versioning → Keep a Changelog + SemVer (this file's
  header note; user-ratified via R1 PR).
- `doc-planner` frontmatter model opus → **sonnet**; Deliberate `--consensus` escalates
  to opus at Task-call time in `docs-plan` (G4 precondition, spec critique #2).
- Routing checkpoint pins **pdf as input/convert layer** (never a generation FORMAT) +
  regression test (H5 decision).
- README Status/Structure refreshed to the current inventory (H6).

### Fixed
- `docs-pdf` skill registered in plugin.json — was shipping dead (H1).
- `docs-pilot` bilingual "식별자 스크럽" confidentiality anchor restored (H2).
- `docs_verify_emit`: dead `DOC_EXTS` constant removed; xlsx engine signals
  (openpyxl/xlsxwriter/Workbook() + xlsx-named scripts) now trigger the reminder (H4).
- `references/themes/` fallback presets wired into docs-build / docs-standardize (H7).

## Historical — pre-semver (commit-SHA era)

### Added
- **Build-time format-regression defense — pptx card API traps + post-build shape-assertion gate + standardize enforcement**
  (response to the 2026-06-16 herolab 5-fail format audit). Audit conclusion: omd's safety leans not on gates but
  on "the fidelity of the card the builder reads", yet `pptx.md` was silent on python-pptx **high-level API traps**
  (sibling `docx.md` already holds the equivalent `paragraph.text` setter trap — a card-to-card asymmetry). Five changes:
  ① `references/formats/pptx.md` gains a "clone the master layouts (no hand-drawn TextBox on a blank slide)" section
  + 3 python-pptx API traps `[VERIFIED ✓ — 2026-06-16, measured on 1.0.2]` (`text_frame.text=` destroys inherited rPr →
  theme Calibri collapse / an unset `font.size` → master 28pt fallback / a `width=0` box → text vanishes) + level-index
  0-base correction. ② `agents/doc-builder.md` Investigation_Protocol gains a **mandatory mechanical assertion step**
  (before rendering, re-open with python-pptx and check font.size present, width/height>0, font matches, no leftover
  placeholder; no handoff before `ASSERT OK` — catches the v4/v5 class a PNG eyeball misses). ③ `agents/doc-verifier.md`
  **re-runs the same assertion independently**, distrusting the builder's `ASSERT OK` (self-approval ban — "opens" ≠ "format
  preserved"). ④ `skills/docs-standardize`·`docs-pilot` make **standardize non-skippable when a template is supplied**
  (extract the layout/placeholder map first). ⑤ **hook contract change** — `hooks/docs_verify_emit.py`'s `is_doc_build`
  now catches the builder's recommended path `python3 build_deck.py` (the detection blind spot of the old "signal AND
  extension" condition); an inline engine signal fires on its own, an unrelated `analyze_runs.py` stays silent (noise
  control preserved); the reminder body now points at the shape-assertion gate. Regression guard `tests/test_verify_emit.py` (9 cases).
- **Two-tier wiki — extended the `wiki_query` contract to local + global ascent merging** (ADAPT backport
  of oms `e47ab44`'s two-tier ascent wiki into the omd domain). The `wiki_query(category)` implementation merges the local
  `.omd/wiki/` + the nearest parent `.omd/wiki/` (global level, discovered via ascent — same as git's `.git`-finding
  approach) and source-tags them `[wiki:local]`/`[wiki:global]`. ⚠️ **Caller signature unchanged** —
  ascent, merging, and tagging are all confined inside the abstract-function implementation, so `doc-inspector` pre-commitment does not change a single
  line (the future MCP swap point stays intact too). Zero absolute paths, env, or XDG (work-root relative). On a missing parent `.omd/`,
  a graceful empty list. Updated: `references/wiki/README.md`, `references/learning-protocol.md` (new §1.4
  "Two wiki levels"), `agents/doc-inspector.md`, `skills/docs-pilot/SKILL.md` (Step 7),
  `skills/docs-learn/SKILL.md` (§4b local→global promotion path). Regression guard `tests/test_wiki_two_level.py`.
  ⚠️ **omd-domain variant (not a wholesale copy of oms)**: ① **dropped** oms's global-only `history/` category (omd has
  no init or document-dedup demand for it, so it's dead) ② oms's global citation ban → omd instead has a **permanent global ban on document content
  (text, claims, numbers, sources)** (a global extension of §6.F content-preservation) ③ **a new cross-
  project confidentiality-isolation gate** (absent in oms — the global wiki is shared across multiple projects, so identifiable project-specific
  content is globally banned, local-only; only abstract form rules are promoted, and `docs-learn` §4b enforces scrubbing).
- **Registered `docs-learn` in plugin.json skills** (drift fix): it existed on disk but was unregistered in plugin.json,
  so it was not loaded on deployment — corrected (it is the skill that owns the two-tier wiki's local→global promotion, so if missing,
  §4b ships dead). Regression guard `tests/test_plugin_integrity.py` blocks skills↔directory 1:1 drift.

### Changed
- **New `references/omc-backport-analysis.md` §4 — reverse-backport review of omp 0.2.0 (0 adopted).**
  Adversarially evaluated whether to reverse-backport the 5 items that sibling omp added in 0.2.0 (content_conventions, content audit, dead-link, CONVENTIONS.md,
  specificity content item) into omd (checked against omd's real source) → all REJECTED.
  omd is a pipeline that generates binary office artifacts, so the rules.json regex audit loop and body/frontmatter
  scope lose their referent, and content verification is handled by the PPTEval 3-axis rubric. The specificity content item is a category that omd
  *already explicitly rejects* in the §3 exclusion table and learning-protocol §5 H6 ("no numeric weighted sum").
  Permanently records "0 reverse adoptions" to prevent repeated re-review. Zero code changes — docs only.
- **Added the xlsx format to the routing hook contract** (`hooks/route_emit.py`, UserPromptSubmit): the FORMAT
  slot held only `pptx|docx|hwpx`, so xlsx work was not recognized in routing — fixed →
  `pptx|docx|xlsx|hwpx`. Updated both the body format list and the STAGE line. The regression test
  `test_context_lists_formats` adds xlsx (11 passed). stdlib only, fail-open maintained.
- **Updated the docs-build card list** (`skills/docs-build/SKILL.md`): docx changed from "stub" → complete,
  xlsx added, pptx equation policy corrected to "matplotlib PNG only (soffice OMML not rendered)".
- **Extended the routing hook contract** (`hooks/route_emit.py`, UserPromptSubmit): added the
  `revise` token to the STAGE catalog — the `docs-revise` skill actually exists but was missing from the STAGE list, fixed
  (`intake|standardize|plan|build|inspect|verify|revise|docs-pilot`). Also injected a cue that, on a Deliberate
  (defense, review, external official presentation) trigger, the `docs-plan --consensus` (RALPLAN-DR) invocation should be stated with a one-line
  rationale. stdlib only, fail-open pattern maintained.

### Added
- **docx format card completed** (`references/formats/docx.md`, STUB→full): python-docx 1.2.0 engine,
  2 equation paths (**OMML editable path A = soffice render VERIFIED** [caveat: `\hat` accent, `\sum` □],
  matplotlib PNG path B fallback), 3 header/footer rules (+ pitfall #1424), PAGE field (simple PAGE = soffice
  render VERIFIED), Korean fonts, `paragraph.text` getter-safe/setter-destructive, JPEG render recipe.
- **xlsx format card created** (`references/formats/xlsx.md`): openpyxl (edit)/xlsxwriter (create) routing,
  `<v>0</v>` formula-cache pitfall (VERIFIED measured — not recalculated by `--convert-to`, needs a calculateAll macro),
  structure-validation gate (not PNG inspection — a spreadsheet trait), openpyxl chart load loss and app.xml pitfall.
- **MCP/official-skills backport analysis doc** (`references/mcp-skills-backport-analysis.md`, new):
  the adopt/exclude mapping for 8 Office MCPs (not adopted, direct python driving is already that engine) + Anthropic official Agent Skills (the source of
  borrowed patterns) + a per-format equation-render measurement matrix + the diff criteria.
- **Routing hook regression tests** (`tests/test_route_emit.py`, new): omd had no `tests/` until now,
  but the hook is a *contract*, so regression verification is needed on change → 9 new tests (UserPromptSubmit emit,
  STAGE contract, 8-stage enumeration (including revise), 3-format enumeration, format-card authority, `--consensus` rationale,
  no label collisions (STAGE(docs)↔STAGE(paper)↔ROUTE), stdlib only, fail-open).
- **OMC backport analysis doc** (`references/omc-backport-analysis.md`, new): a permanent record of where the 4 techniques deepen, consensus, and
  critic came from in OMC 4.14.4 and what was excluded — the basis for judging updates when OMC updates.

### Verification
- `pytest tests/` — 11 passed (route_emit regression, including xlsx format addition).
- Both hooks pass `python3 -c "import ast; ast.parse(...)"` + emit valid JSON when run
  (confirmed to include `revise`, `--consensus`, `xlsx`).
- **Equation/pitfall measurements** (2026-05-31): docx OMML soffice render PNG eye-checked (PoC1, PoC2), pptx OMML blank
  re-confirmed (PoC3), docx PAGE field "page 2" render confirmed (PoC4), xlsx `<v>0</v>` cache + `--convert-to`
  no-recalculation confirmed (PoC5b). Every VERIFIED claim in the cards is backed by an actual render PNG.
