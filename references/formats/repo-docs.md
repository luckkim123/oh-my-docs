# repo-docs — GitHub repository documentation set (genre card)

> **What this is**: a *genre* card, not an engine card — the engine is plain Markdown plus a
> borrowed linter chain. Single source of truth for producing the GitHub repository document
> set: README.md, CHANGELOG.md, community health files, issue/PR templates, CODEOWNERS.
> Layout SSOT: `references/output-layout.md` — this genre is an **artifact-set**
> (`outputs/<slug>/current/` directory + `.omd/<slug>/manifest.json`).

## Engine

| Tool | Role | Version (measured) | Status |
|:---|:---|:---|:---|
| Markdown (CommonMark/GFM) | the format itself | n/a | no engine to install |
| markdownlint-cli2 (via `npx`) | gate ③ lint | — | UNVERIFIED (not yet measured on this machine) |
| lychee | external-link check (optional item) | — | UNVERIFIED — optional; network-dependent, excluded from the default gate |
| python3 stdlib | section-order / date / placeholder checks | measured at dogfooding | see `tests/test_repo_docs_dogfood.py` |

Engine-missing rule (D3): a required engine that is not installed yields the verdict
`UNVERIFIED (engine unavailable)` for that item — state honestly what was not checked.
Never a silent PASS, never a FAIL on the environment. (Engine-drift demotion per
`references/formats/README.md` applies once versions are pinned.)

## Artifact set + intake scope gate

Covered files: `README.md` (standard-readme) · `CHANGELOG.md` (keep-a-changelog 1.1.0) ·
`CONTRIBUTING.md` / `SECURITY.md` / `CODE_OF_CONDUCT.md` / `SUPPORT.md` ·
`.github/ISSUE_TEMPLATE/*` + `PULL_REQUEST_TEMPLATE.md` · `CODEOWNERS`.

**Intake set-scope gate (set genre — Gate 0 supplement)**: before format·kind, lock which
subset this request produces — *full set* / *README only* / *community-health only*. The
choice lands in the manifest's `role` fields (D4). Do not silently produce 8 files for a
README request.

**doc-analyzer input boundary (AC-3)**: never read the whole codebase. Whitelist: existing
README/CHANGELOG/community-health files, package manifests (package.json, pyproject.toml,
plugin.json, …), CI config, a Grep/Glob *structure* scan (paths, not full contents), and a
recent commit-log summary.

## Structure frames (what doc-planner consumes instead of a narrative arc)

**README — standard-readme required order**: Title → Short Description (≤120 chars) →
ToC (**required at 100+ lines**, a violation on short files) → Install → Usage →
Contributing → License (**always last**). Optional: Badges (right after title), Background,
Security, API, Maintainers.

**Genre section presets** (this genre's no-reference fallback — `references/themes/` office
palettes do NOT apply here, F8):
- `library`: Title → Badges → Short Desc → Install → Usage (API) → Contributing → License
- `cli`: Title → Badges → Short Desc → Install → Usage (commands table) → Contributing → License
- `dataset`: Title → Short Desc → Access/Download → Schema → License/Citation → Contributing

**CHANGELOG — keep-a-changelog 1.1.0**: `[Unreleased]` on top; one `## [x.y.z] - YYYY-MM-DD`
section per release, ISO 8601 dates, versions descending; exactly six change types
(Added / Changed / Deprecated / Removed / Fixed / Security); `[YANKED]` suffix for pulled
releases. Guiding principles: changelogs are for humans; every version gets an entry;
same types grouped; linkable versions; latest first.

**Community health files**: GitHub resolves them from three locations — repo root,
`.github/`, `docs/` — plus an org-level `.github` repository fallback (public repos;
LICENSE never falls back). Issue templates live at the fixed path `.github/ISSUE_TEMPLATE/`
with required frontmatter (`name`, `about` — form schema: `description`).

## Hard traps

- **CODEOWNERS — last match wins**: put specific rules at the BOTTOM (opposite of most
  ignore-file intuitions). Multiple owners for one pattern must share ONE line. A
  syntactically wrong line is **silently skipped** (GitHub raises no error — only a checker
  catches it). Paths are case-sensitive. [source: GitHub docs — Sources below]
- **README ToC**: standard-readme requires a ToC only at 100+ lines — adding one to a short
  README violates the spec exactly as omitting one from a long README does (gate ①). [source: standard-readme spec — accessed 2026-07-11]
- **Placeholder look-alikes**: markdown link syntax `[text](url)` is legitimate — the
  placeholder scan (gate ⑦) targets prompt tokens (`[Insert …]`, TODO, TBD, CHANGEME,
  `your-*-here`, lorem), not link brackets. A naive `\[.*\]` grep false-positives on every
  link; scan for the token patterns. [source: omd PL-3 design, spec §3.4 — 2026-07-11]
- **Badge markdown**: a badge is an image-link `[![alt](img-url)](target-url)` — a bare
  image or a dead target reads as neglect (gate ⑥ checks form; target liveness is the
  optional lychee item). [source: shields.io/GitHub badge convention — accessed 2026-07-11]

## Verify gate (docs-verify / doc-verifier run this — deterministic, exit-code first)

| # | Check | How |
|:--|:---|:---|
| ① | Required sections present + in preset order | stdlib heading parse vs the chosen genre preset |
| ② | Internal links & anchors resolve | relative paths exist; heading anchors match. External links: **optional** lychee item — network-dependent, excluded from the default gate (spec §7 ③) |
| ③ | markdownlint-cli2 passes | `npx markdownlint-cli2 <files>`; missing engine → D3 degrade |
| ④ | Every fenced code block carries a language tag | stdlib fence scan |
| ⑤ | CHANGELOG: ISO 8601 dates + semver sections descending + `[Unreleased]` first + only the six types | stdlib parse (legacy pre-semver `## Historical` tail section exempt — omd-specific note) |
| ⑥ | Badge markdown well-formed | image-link form check |
| ⑦ | **Placeholder scan** — prompt tokens (`[Insert …]`, TODO, TBD, CHANGEME, `your-*-here`, lorem): any hit = FAIL (PL-3) | grep for token patterns, not bare brackets |

Log capture (AC-1b): every borrowed-engine run's stdout+stderr →
`.omd/<slug>/verify-runs/<engine>-<timestamp>.log`, linked from the report.

Layer frame — the "linting ladder" (checkable → customizable → blameable → fixable;
**McNutt et al. 2024**, cited via the LintMe paper, CHI 2026): gate items ①②④⑤⑥⑦ are
*checkable*, ③ is *customizable* (config-driven); qualitative axes belong to the rubric
(`references/rubrics/repo-docs-rubric.md`), never to this gate.

## Version-snapshot policy

Artifact-set: a snapshot copies the **whole** `outputs/<slug>/current/` directory to
`.omd/<slug>/versions/v{NN}_{YYYY-MM-DD}_{summary}/` (LC-1; output-layout §3.3). Same
"only before a large edit" rule; manifest.json is rewritten atomically (ST-1) after any
member change.

## Placement (LC-2 — the user publishes, omd does not)

Deliverables stay in `outputs/<slug>/current/`. The manifest `role` field records each
file's repo-relative target (`README.md` → repo root; templates → `.github/ISSUE_TEMPLATE/…`;
`CODEOWNERS` → root, `.github/`, or `docs/`). Guidance: `cp -r` preserving relative paths per the
`role` map. omd never writes into the user's repository itself (§8: producing is omd's
lane, publishing is the user's).

## Form vs content (D7 boundary — this genre's examples)

Learnable FORM: section-order preference, voice/tone, badge style, changelog grouping
convention. Permanently forbidden CONTENT: project facts, API names, version numbers,
link targets.

## License_Note

Standards referenced (structure only, no text copied): standard-readme spec ·
Keep a Changelog 1.1.0 · GitHub community-health/template/CODEOWNERS docs · The Good Docs
Project template pack (structural seed for docs-standardize's "no sample supplied" case).

## Sources

- standard-readme: https://github.com/RichardLitt/standard-readme/blob/main/spec.md
- Keep a Changelog 1.1.0: https://keepachangelog.com/en/1.1.0/
- Google README guide: https://google.github.io/styleguide/docguide/READMEs.html
- Community health files: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file
- Issue/PR templates: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates
- CODEOWNERS: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- LintMe (CHI 2026, arXiv 2603.00331) — ladder attributed to McNutt et al. 2024 ("Mixing linters with GUIs")
- The Good Docs Project: https://www.thegooddocsproject.dev/
