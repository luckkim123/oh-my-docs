# Changelog

All notable changes to oh-my-docs (omd).

> **Versioning policy**: omd deliberately uses **commit-SHA versioning** (no individual release numbers).
> This file tracks only the *contract change history* — when a surface that other
> components (omha, the session LLM) depend on changes, such as a hook's emit format, it is recorded here. General content
> changes have the git log as the SSOT. Tone unified with the OMS (oh-my-scholar) CHANGELOG.

## [Unreleased]

### Added
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
