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

## [0.6.3] - 2026-07-24

### Fixed

- **`docs_verify_emit` armed a `verify-pending` sentinel on read-only commands
  that merely NAMED an engine string** (arm-side false positive, the sibling
  axis to v0.6.2's clear-side leak). `is_doc_build` fired whenever a
  `BUILD_SIGNALS` substring appeared, with no check that the command actually
  runs the engine — so in a workspace with an existing `.omd/`, a grep whose
  search pattern listed engine strings (`grep -E 'openpyxl|Presentation|
  --convert-to' hooks/`) and an openpyxl load-and-print dump of an xlsx
  template (the 2026-07-24 live incident: `cd; cp` a template from a volume;
  `python3 -c 'load_workbook(...); print(...)'`) both armed a slugless root
  sentinel, and the Stop guard re-warned `(slug unknown)` all session.
  `is_doc_build` now nullifies the engine signal when the command is a
  read-only inspection — a leading text viewer (`grep`/`rg`/`egrep`/`cat`/
  `bat`/`less`/`head`/`tail`/… , past optional `cd DIR &&` and an optional
  `git ` for `git grep`), or an `openpyxl` `load_workbook` with no write
  indicator (`Workbook()`/`.save(`/`xlsxwriter`/`create_sheet`). A doc-named
  script run (`RUN_SCRIPT_RE`, e.g. `build_deck.py | tail`) still counts, and a
  genuine slugless build (`python3 build_deck.py`) still arms the root sentinel
  — the deliberate design v0.5.1 pinned, with G7's 7-day self-expiry as its
  safety net — so this narrows the *non-build* case only, the same intent as
  `TEST_RUN_RE`. The viewer regex's directory class excludes whitespace so a
  long `cd a && …` chain cannot trigger catastrophic backtracking (a 200-char
  command hung `is_doc_build` ~6 s before the fix; `main()` runs it outside the
  fail-open envelope, so a hang would have frozen the turn). Known accepted
  ceilings (documented in-code): an exotic viewer prefix (`sudo`/`time`/
  `LC_ALL=C`/subshell) still re-arms, and a leading viewer guarding an inline
  `python3 -c` engine build is silenced — both low-likelihood, the
  advisory-safe direction. No clear-side or slug-context change.
- **Two relevance-gate silence tests were not hermetic**: they inherited
  pytest's cwd, so on a dogfooded checkout (untracked `.omd/` at the repo
  root) `_has_omd_marker()` forced injection and the silence assertions
  false-failed (clean worktrees and CI passed -- 2026-07-21 finding while
  releasing v0.6.2). Both now pin `cwd=tmp_path` like their marker-aware
  sibling tests already did. Test-only change; hook behavior untouched.
- Verification: 10 new regression tests in `tests/test_verify_emit.py` — the
  false-positive shapes stay silent and arm nothing (grep for engine strings,
  ripgrep/cat, `head`/`tail`/`git grep`, read-only openpyxl dump, and the live
  `cd; cp; load_workbook` compound), while genuine builds still fire (openpyxl
  edit-and-save incl. `.save (` spacing, `Workbook()` construction,
  `build_deck.py` piping to `tail`); plus a latency guard asserting the viewer
  regex stays sub-500 ms on a 328-char `cd a && …` chain (ReDoS regression).
  Post-review adversarial pass (2026-07-24) reproduced and closed the
  backtracking hang and the `head`/`tail`/`git grep` prefix gap. Full suite
  green: 274 passed, 2 skipped (`tests/test_verify_emit.py` +
  `tests/test_stop_guard.py`: 72 passed).

## [0.6.2] - 2026-07-21

### Fixed

- **`clear_sentinels` missed the real slug sentinel when the verify signal ran
  from inside the slug directory** (D1). A relative-path render (`pdftoppm`)
  with cwd under `.omd/<slug>/` carries no `.omd/<slug>/` in its command string
  for `SLUG_RE`, and `<cwd>/.omd` resolved to a nonexistent path, so the clear
  returned early — the sentinel survived and the Stop guard re-warned all
  session long (2026-07-21 utracker-seminar incident, 8+ repeats).
  `docs_verify_emit.py` now derives the project `.omd` root and the slug from
  the cwd path COMPONENTS (`.omd/<slug>/` or `outputs/<slug>/` anchors —
  substrings like `test_outputs/` do not match) whenever the command names no
  slug. A cwd-identified clear removes ONLY that slug's sentinel — the broad
  fallback was not widened. Commands that do name a slug, and the fully
  slugless broad fallback, behave exactly as before. Arming from inside the
  slug directory (same defect class — it used to be skipped silently) now arms
  the correct slug sentinel.
- **The Stop guard had no per-turn suppression for carried-over sentinels**
  (D2). `stop_hook_active` only prevents re-entry inside one Stop, so a
  carried-over sentinel (no TTL — HK-4) re-warned at EVERY Stop of a session.
  `docs_stop_guard.py` now announces a given carried-over set (armed_at past
  `STALE_AFTER`, the same 6h proxy the "carried over" tag uses) once per
  session, keyed by Stop-payload `session_id` + the stale slug set, stored in
  the shared HG-3 throttle file (`.omd/.hook-throttle.json`, atomic write).
  HK-4 ("real carried-over work stays visible") is kept, refined: sentinels
  still never expire and every new session re-surfaces them at its first Stop;
  fresh sentinels keep warning at every Stop, unchanged.
  `OMD_REMINDER_COOLDOWN_SECONDS<=0` disables the suppression (the same HG-3
  kill switch); payloads without `session_id` are never suppressed (fail-open
  toward visibility).
- Verification: 9 new regression tests — 4 × D1 in `tests/test_verify_emit.py`
  (clear from inside `.omd/<slug>/`, slug-specific clear only,
  `outputs/<slug>/` cwd, arm from inside the slug dir) and 5 × D2 in
  `tests/test_stop_guard.py` (once per session + re-notice in a new session,
  fresh warns every Stop, mixed fresh/stale second Stop, no `session_id` → no
  suppression, env kill switch). Full suite green: 264 passed, 2 skipped
  (`python3 -m pytest`, exit 0). Pre-existing no-change guards untouched:
  slug-in-command clear, slugless broad-fallback clear, slugless 7-day G7
  expiry, slugged no-TTL (HK-4).

## [0.6.1] - 2026-07-19

### Fixed

- **The 3 inline atomic-write copies in `docs_precompact_reinject.py` and
  `docs_verify_emit.py` never called `fsync`**, so a power loss between
  `os.replace` and the OS flushing its page cache could still lose the write.
  Now routed through a new vendored `hooks/omd_atomic.py` (from the shared
  `om-core` repo), which fsyncs before replace. Hook imports use the
  `sys.path.insert(0, str(Path(__file__).parent))` + bare `import omd_atomic`
  form (matching omp's pattern) rather than `hooks.omd_atomic`, since these
  hooks run both as a direct subprocess (`sys.path[0]` is the `hooks/` dir) and
  as a package import under pytest — a package-qualified import only resolves
  in the second context. The throttle write keeps its `try/except Exception:
  pass` guard unchanged (a throttle-write error must not suppress the verify
  reminder) and gained an explicit `os.path.isdir(root)` guard — the vendored
  `atomic_write_json` mkdirs its parent unconditionally, which would otherwise
  fabricate `.omd/` in a non-omd repo (the old inline `tempfile.mkstemp`
  silently failed instead, matching `arm_sentinel`'s existing noise-control
  guard). The sentinel write drops its now-redundant `os.makedirs` call — the
  vendored function mkdirs the parent itself — and its format changes from
  compact to pretty-printed JSON, safe because both readers (`test_verify_emit.py`,
  the throttle reader) already parse via `json.load`/`json.loads`,
  format-agnostic. Adds a local-only `tests/test_atomic_vendored_sync.py` that
  byte-compares the vendored copy against `~/om-core/atomic_fn.py` and skips
  gracefully when that sibling repo is absent (clean CI).

## [0.6.0] - 2026-07-19

### Added

- **`references/snippets/` — canonical render/assert code library** (design:
  `.sp/specs/2026-07-19-omdsnip-design.md`): four single-purpose reference-implementation files
  (`render.py`, `integrity.py`, `assert_shapes.py`, `engine_check.py`) plus a contract README,
  each copy/adapt-only per the "rebuild, don't wrap" audit rule — never imported by an agent at
  runtime, only by this repo's own test suite. Closes a real correctness risk (not just a
  token-cost one): `doc-builder`'s self-gate shape assertion and `doc-verifier`'s independent
  re-run now point at the exact same `assert_shapes()` function instead of two hand-derived
  copies that could silently diverge. Also codifies the OOXML 5-way closure scan
  (`integrity.py`), the soffice/pdftoppm render recipe (`render.py`), and the G7
  engine-version-drift check (`engine_check.py`) — each previously re-derived from prose on
  every job. Pointer lines (`` Canonical implementation: `references/snippets/<file>.py::<function>`. ``)
  added to `pptx.md`, `docx.md`, `xlsx.md`, `references/formats/README.md`, `doc-builder.md`,
  `doc-verifier.md` (6 files — `hwpx.md`/`pdf.md` deliberately excluded, see design Out-of-scope).
  4 new test files, all import-clean and collection-safe with no optional library installed
  (`pptx`/`pypdf`/`soffice`/`pdftoppm` absent), verified against the clean-CI shape in
  `.github/workflows/ci.yml`. No behavior change to any agent — only the copy-paste source they
  already used improves.

## [0.5.4] - 2026-07-19

### Fixed

- **Hook filename collision with sibling plugin** (audit finding): `hooks/route_emit.py`,
  `hooks/model_guard.py`, and `hooks/precompact_reinject.py` shared a bare basename with
  hooks of the same name in the sibling `oh-my-heroacademia` plugin, making traces ambiguous
  when both plugins are loaded. Renamed to `docs_route_emit.py`, `docs_model_guard.py`, and
  `docs_precompact_reinject.py` to match the `docs_` convention already used by
  `docs_stop_guard.py`/`docs_verify_emit.py`. Updated `.claude-plugin/plugin.json`, the three
  corresponding test files, and the README hooks/ layout diagram.

### Added

- **CI workflow** (`.github/workflows/ci.yml`): runs the test suite on push to `main` and on
  pull requests via `actions/checkout@v4` + `actions/setup-python@v5` (3.11) + `pytest`.

## [0.5.3] - 2026-07-16

### Fixed

- **docs_stop_guard: slugless sentinels self-expire after 7 days** (2026-07-15 vault
  incident, second instance of the v0.5.1 false-positive class: a robotics deploy+test
  pipeline — `python3 -m pytest ... test_obs_builder.py` over ssh/docker — matched "build"
  inside "obs_builder", armed a top-level `.verify-pending` in a workspace with no document
  history, and the Stop guard re-warned "(slug unknown)" at every session Stop with no
  expiry path). A slugless root sentinel names no `.omd/<slug>/` workspace, so nothing ever
  resolves it where verify signals never run: past `SLUGLESS_EXPIRE_AFTER` (7 days) it is
  now removed with one final notice. Slugged sentinels keep HK-4 semantics — real
  carried-over work never expires. This also auto-cleans sentinels already planted in
  foreign repos before the v0.5.1 arm guard shipped (they predate the fix on every machine).
  3 tests (expiry + fresh-slugless boundary + slugged-never-expires).
- **Vault incident command pinned verbatim as a regression test**: the multi-line
  ssh + docker exec pipeline exercises a distinct path from the v0.5.1 oh-my-scholar
  incident — a doc keyword inside a non-`test_`-prefixed word ("obs_builder"), where only
  the standalone-token pytest exclusion prevents the match.

## [0.5.2] - 2026-07-16

### Fixed

- **route_emit's SSOT-gate wiki category list matched to code** (2026-07-16 om* wiki audit
  finding): the per-turn injected `.omd/wiki/(convention·technique·pattern)` parenthetical
  named a category that does not exist anywhere (`technique`) and omitted the real
  `decision`/`reference` — every session was pointed at a nonexistent directory and never told
  about two real ones, silently weakening the SSOT-first gate the hook exists to enforce. Fixed
  to `(convention·pattern·decision·reference)`; a new locking test binds the hook prose to
  `references/wiki/lint_wiki.py` CATEGORIES so the two can never drift apart again — the live
  instance of the "hook prose restates a code fact with no test binding them" failure class.
- **TEST_RUN_RE standalone-token guard** (v0.5.1 verifier finding, committed post-release)
  ships in this release.

## [0.5.1] - 2026-07-16

### Fixed

- **docs_verify_emit no longer mistakes test runs for document builds, and never
  fabricates `.omd/` outside an omd project** (2026-07-16 false-positive: a sibling
  harness's `pytest tests/test_wiki_spec_docs.py` run matched the doc-keyword script
  heuristic — "doc" inside a TEST filename — and armed a top-level `.verify-pending`
  in a foreign repo whose `.omd/` the hook itself created; the Stop guard then
  re-warned "(slug unknown)" every turn until manual cleanup). Two guards: a
  word-level `pytest`/`unittest` exclusion plus a `test_*`/`*_test.py` filename
  filter on the captured script name, and `arm_sentinel` now requires an existing
  `.omd/` root (mirrors handle_md_edit's no-slug-context rule). The integrity
  reminder itself still fires for genuine build commands outside a project — only
  the persistent sentinel is scoped. 3 regression tests (incident command verbatim);
  6 existing arm/clear/cooldown tests updated to pre-create `.omd/` per the new contract.
- `references/wiki/lint_wiki.py` docstring now records WHY two omx lint checks were
  not ported (`contradiction-candidate`, `low-confidence`/`low-quality` — omd notes
  carry neither tags nor quality_score), previously an undocumented divergence.
- `references/wiki/README.md`: "identical across every om* harness" precision — the
  `status:`/`blocked-on:` key NAMES are family-wide, the value vocabulary is
  per-harness (omx/omd/oms listed explicitly).

## [0.5.0] - 2026-07-14

### Added
- **Actionable-status wiki convention (family wiki-status backport)** — `references/wiki/README.md`,
  `references/wiki/lint_wiki.py`, `skills/docs-verify/SKILL.md`, `skills/docs-learn/SKILL.md`,
  `tests/test_wiki_lint.py`. A wiki note may now carry an optional `status: needs-revision | resolved`
  frontmatter field (plus `blocked-on: <free text>` while open). `needs-revision` marks a measured
  style/spec correction that is recorded but not yet applied; `resolved` is terminal; **absent = not
  actionable** (every existing note). This closes the om*-family failure mode where an actionable
  finding is archived in the wiki yet silently dropped before the next build/promotion.
  - `lint_wiki.py` gains two report-only findings (still exit 0, WARN-never-gate): `open-revision`
    enumerates every open `needs-revision` note keyword-independently, and `unknown-status` flags a
    mistyped value (which would otherwise silently leave the enumeration).
  - `docs-verify` (step 3b) and `docs-learn` (step 0) now surface open `needs-revision` notes as a
    named WARN before a build / style-promotion — a measured correction cannot be built or promoted
    over unknowingly. WARN only; omd never hard-gates on the wiki.
  - Enumeration stays omd's "grep only" contract: `grep -rlE '^status:[[:space:]]*needs-revision[[:space:]]*$'
    .omd/wiki/` is the family-wide fallback (the on-disk `status:`/`blocked-on:` keys match every om* harness).
  - Backwards compatible / additive-optional: notes without a `status` key never surface and are
    byte-unchanged; the linter stays report-only (exit 0). No new subsystem, storage, or scheduler —
    the existing `lint_wiki.py` is the enumeration surface and docs-verify/docs-learn are the boundary.

## [0.4.0] - 2026-07-14

R4 "knowledge lifecycle" — the capture-then-curate loop closes: query helpers make the
wiki safely writable and searchable across CJK/English, lint gives it a health signal,
notepad survives compaction, and stop-guard/ownership gates keep pilot runs honest
(spec: `docs/superpowers/specs/2026-07-11-omd-program-design.md` §5 R4).

### Added
- **`query_helper` wiki write/query guards**: CJK bi-gram tokenizer + match (KN-2, README
  contract repayment), `safe_wiki_path` resolve-prefix guard against symlinked category
  escape (KN-3), `title_to_slug` English slug rule (KN-4) — wired into `docs-pilot` Step 7
  and `docs-learn` Steps 4/6.
- **`lint_wiki` (G3)**, adapted from omx — a report-only store auditor; `docs-learn` Step 0
  now runs it as a wiki health report before promotion.
- **`precompact_reinject` hook (G2)**: notepad 3-tier contract, prunes on `PreCompact` and
  reinjects on `SessionStart(compact)` so pilot state survives context compaction.
- **Stage-evidence markers + stop-guard gap grep (G5)**: `docs_stop_guard` gains a second
  advisory check beyond G1's verify-pending reminder — flags recent pilot runs (within
  `STALE_AFTER`) missing stage markers; `docs-pilot` now emits the markers it checks for.
- **Ownership guard (G6)**: manifest-checked overwrite/delete gate in
  `references/output-layout.md` §3.4, wired into `docs-build`/`docs-pilot`/`docs-revise`
  and `doc-builder`.
- **OBS capture path (§4.5c)**: `docs-pilot` Step 7b plus 3 observing stages
  (`docs-inspect`, `docs-standardize`, `docs-verify`) complete the capture-then-curate
  loop — observations captured during those stages now have a defined path into the wiki.

### Changed
- **Wiki README contract** (`references/wiki/README.md`): CJK bi-gram tokenizer pointer
  (KN-2), home-directory ascent floor for the global-wiki search (ST-3), English slug rule
  (KN-4), and `safe_wiki_path`/`title_to_slug` write-site wiring (KN-3/KN-4) documented
  alongside the existing two-level contract.
- **`docs-learn` Step 0** now wires in the wiki lint health report (G3) ahead of promotion.
- **`docs_stop_guard`** extended past its original G1 verify-pending reminder (0.1.0) to
  also run the G5 stage-marker gap grep — same hook, same advisory/fail-open/re-entry-safe
  posture, second check.

> **Verification**: `python3 -m pytest -q` — 175 passed (R3 baseline 136).

> **Notes**: LOCAL ONLY — marketplace update + app restart required after merge (spec §7
> ⑤). This closes the R1–R4 knowledge-lifecycle release train (spec §5).

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
