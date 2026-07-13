# site — MkDocs + Material documentation site (genre card)

> **What this is**: a *genre* card — the deliverable is a static documentation site whose
> **source** is an artifact-set (`outputs/<slug>/current/` = `mkdocs.yml` + `docs/` tree,
> plus `.omd/<slug>/manifest.json`; layout SSOT: `references/output-layout.md`). The build
> engine is borrowed (MkDocs + Material). Built HTML is a *derived* artifact — it lives in
> the work area (`.omd/<slug>/site-build/`), never inside `current/`.
> Documented alternative (R5+, no card): Docusaurus — Node/React ecosystem,
> `onBrokenLinks: 'throw'` as its machine gate.

## Engine

| Tool | Role | Version (measured) | Status |
|:---|:---|:---|:---|
| MkDocs (via `uvx --from mkdocs --with mkdocs-material mkdocs`) | build + `--strict` machine gate (gate ①) | — | UNVERIFIED (initial — the R3 measurement task stamps this machine) |
| mkdocs-material | theme; its `palette:` schema is this genre's no-reference fallback (F8) | — | UNVERIFIED |
| markdownlint-cli2 (via `npx`) | gate ② lint | v0.23.0 (markdownlint v0.41.0) | VERIFIED ✓ — 2026-07-13, markdownlint-cli2 v0.23.0 (R2 stamp, same runner) |
| lychee | external-link check (optional item) | — | UNVERIFIED — optional; network-dependent, excluded from the default gate |
| python3 stdlib | nav-completeness / placeholder / link fixture checks | measured at dogfooding | see `tests/test_site_dogfood.py` |

Runner note (measured 2026-07-13): the verified invocation is **ephemeral** —
`uvx --from mkdocs --with mkdocs-material mkdocs …` (uv-managed Python; a system
python3 too old for the toolchain is irrelevant to this path). No global install is
required or wanted; the runner form above IS the verified path.

Engine-missing rule (D3): a required engine that is not installed yields the verdict
`UNVERIFIED (engine unavailable)` for that item — state honestly what was not checked.
Never a silent PASS, never a FAIL on the environment. (Engine-drift demotion per
`references/formats/README.md` applies once versions are pinned.)

## Structure frame — Diátaxis quadrants (what doc-planner consumes)

Map the outline onto the four Diátaxis quadrants — the axes are *action vs cognition* ×
*acquisition vs application*:

| Quadrant | Serves | Form |
|:---|:---|:---|
| tutorials/ | learning by doing | a lesson — safe, guaranteed steps |
| how-to/ | a goal at work | a recipe — assumes competence |
| reference/ | information lookup | dry, complete, structured facts |
| explanation/ | understanding | discussion of why — context, design, trade-offs |

Rules doc-planner applies: one page serves ONE quadrant (mixing tutorial and reference on
a page is the classic failure); the nav's top level mirrors the quadrants; keep nav depth
≤ 2 (two-click reachability); every quadrant present or its absence justified in the
outline. Intake scope for this set genre: full site / a single quadrant / single-page
revision — the choice lands in the manifest `role` fields (D4).

## Standard mkdocs.yml skeleton (the validation block is NOT optional)

```yaml
site_name: <name>
theme:
  name: material
  palette:            # no-reference fallback (F8): pick primary/accent + scheme here,
    - scheme: default #   never from references/themes/ (office palettes)
      primary: indigo
      accent: indigo
validation:           # REQUIRED — without this block, `--strict` passes builds that
  nav:                #   silently drop pages (see Hard traps)
    omitted_files: warn
    not_found: warn
    absolute_links: warn
  links:
    not_found: warn
    anchors: warn
    unrecognized_links: warn
nav:
  - Home: index.md
  # top level mirrors the Diátaxis quadrants
```

## Hard traps

- **`--strict` alone does not catch nav-omitted pages** — `mkdocs build --strict` aborts
  on WARNING, but a `docs/**.md` file missing from `nav:` emits INFO by default, so a page
  can silently drop out of a green strict build. The `validation: nav: omitted_files: warn`
  line promotes it to WARNING = strict failure. [source: MkDocs user guide (configuration
  › validation) — accessed 2026-07-13 · candidate, the R3 measurement task promotes this
  with observed log lines]
- **Default output lands inside the source set** — `mkdocs build` writes `site/` next to
  `mkdocs.yml`, i.e. *inside* `outputs/<slug>/current/`, breaking the D4 invariant (the
  current entry is the source set, exactly one entry). Always build with
  `-d <workspace>/.omd/<slug>/site-build` — built HTML is derived evidence, the text
  edition of `renders/current/`. [source: omd D4 output-layout invariant, R3 plan 결정 4 —
  2026-07-13]
- **mkdocs-material config-key drift across majors** — Material renames/moves theme keys
  between major versions; a copied config from an old blog post fails on current Material.
  Pin behavior by measuring on this machine (Engine table), not by trusting snippets.
  [source: Material for MkDocs changelog/upgrade guide — accessed 2026-07-13 · candidate,
  promote with the measured Material version]
- **CJK search** — Material's built-in search tokenizes CJK poorly by default (`lang`/
  `separator` tuning or a plugin may be needed). Verify by inspecting the generated
  `search_index.json` for CJK tokens before promising search over Korean pages.
  [source: Material for MkDocs (search setup) — accessed 2026-07-13 · candidate, measure
  when a Korean page enters a pilot]

## Verify gate (docs-verify / doc-verifier run this — deterministic, exit-code first)

| # | Check | How |
|:--|:---|:---|
| ① | `mkdocs build --strict` exit 0 — **with the card's validation block present** | `uvx --from mkdocs --with mkdocs-material mkdocs build --strict -f <slug>/current/mkdocs.yml -d <workspace>/site-build`; missing engine → D3 degrade |
| ② | markdownlint-cli2 passes over `docs/` | `npx markdownlint-cli2 "outputs/<slug>/current/docs/**/*.md"`; missing engine → D3 degrade. Config discovery follows markdownlint-cli2 (a project-root config may relax rules) — the report names which config applied |
| ③ | Internal links & anchors resolve | covered by ①'s `validation.links` (not_found/anchors: warn + strict). External links: **optional** lychee item — network-dependent, excluded from the default gate |
| ④ | Built-HTML fresh-read | Read representative built pages from `.omd/<slug>/site-build/` — the render read-through, text edition. "The build ran" is not "the site is right" |
| ⑤ | nav completeness — every `docs/**.md` is in `nav:` | covered by ①'s `validation.nav.omitted_files: warn` + strict; the always-on stdlib double-check lives in the permanent guard (`tests/test_site_dogfood.py`), not in this gate |

Log capture (AC-1b): every borrowed-engine run's stdout+stderr →
`.omd/<slug>/verify-runs/<engine>-<timestamp>.log`, linked from the report.

## Version-snapshot policy

Artifact-set: a snapshot copies the **whole** `outputs/<slug>/current/` directory to
`.omd/<slug>/versions/v{NN}_{YYYY-MM-DD}_{summary}/` (LC-1; output-layout §3.3). Same
"only before a large edit" rule; `manifest.json` is rewritten atomically (ST-1) after any
member change. Built HTML (`site-build/`) is derived — never snapshotted.

## Placement (LC-2 — the user publishes, omd does not)

Deliverables stay in `outputs/<slug>/current/`. Publishing (GitHub Pages, `mkdocs
gh-deploy`, any hosting) is the user's lane — omd never deploys (§8). The manifest `role`
field records each file's site-relative place (`mkdocs.yml` → site root; pages → their
`docs/`-relative path).

## Form vs content (D7 boundary — this genre's examples)

Learnable FORM: nav-depth preference, palette scheme choice, quadrant balance, page-length
convention. Permanently forbidden CONTENT: page facts, API names, link targets, code
snippets' substance.

## Sources

- Diátaxis: https://diataxis.fr/
- MkDocs configuration & validation: https://www.mkdocs.org/user-guide/configuration/
- Material for MkDocs: https://squidfunk.github.io/mkdocs-material/
- markdownlint-cli2: https://github.com/DavidAnson/markdownlint-cli2
- lychee: https://github.com/lycheeverse/lychee
