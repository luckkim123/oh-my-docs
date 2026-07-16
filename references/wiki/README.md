# references/wiki — accumulated secondary-memo store (specializes the more you use it)

This store **compounds session-volatile data into a "lab standard"** persistent memo. It runs as a **two-way loop**:
- **Write (automatic)**: docs-pilot's wiki-capture step **auto-appends** the defect patterns / induced style specs / decisions that inspect/verify/standardize surfaced this session (no approval — the light channel, `docs-pilot/SKILL.md` Step 7).
- **Read (automatic)**: the next session's doc-inspector pre-commitment pulls those accumulated patterns via `wiki_query(category)`.

Write and read close the loop, so **the harness specializes to this presentation type / this org's standard the more it is used** — without the user ever explicitly saying "learn this." Ships empty (generic); diverges as it operates.

It is the current backing for the `wiki_query(category)` abstract function, and nothing breaks when it is empty or absent (the inspector proceeds on its own prediction).

---

## Directory layout

⚠️ **The data accrues in the work area (`.omd/wiki/`) — NOT in this plugin repo.** This README is the *contract*, so it ships inside the plugin (`references/wiki/README.md`), but the accumulated data is written to **`.omd/wiki/` under the target project root** (`.omd/` is gitignored — it never dirties the plugin/distributable and diverges per project, which is what makes "specializes to *this* project" hold). Same pattern as OMC's `.omc/wiki/` (project-local).

### ⭐ Two levels — local (this project) + global (parent `.omd/`, found by ascent)

`.omd/wiki/` lives at **two levels**. Both are cwd-relative — **no absolute path, no env var, no XDG** (omd's "relative to the work root" philosophy from `output-layout.md`, so the distributable is never dirtied):

```
<documents' parent folder>/.omd/wiki/   ← ⭐ GLOBAL level — assets this *user/org* reuses across every document
  convention/   *.md   ← org/lab standard style-spec + per-type form rules (reused across docs) — scope = global | <type-key>
  pattern/      *.md   ← disposition (favored phrasing/layout/working-style/preferences) — light only
  decision/     *.md   ← reusable decisions ("defense decks always lead with the contribution slide")
        ▲  discovery = ascent (cwd→parent, the nearest ancestor .omd/, excluding self; git's .git-lookup)
        │   ⚠️ the ascent never climbs above the user's home directory (ST-3) — the home
        │   directory is the hard lower bound, so unrelated projects can never merge through
        │   an accidental common ancestor above it (the confidentiality gate stays intact
        │   on shallow trees).
        │
<project root>/.omd/wiki/                ← LOCAL level — specific to THIS document project (outside <slug>/, carries across sessions)
  convention/   *.md   ← this project's defect patterns + induced style specs (inspector reads this) — ⭐ source of heavy-channel candidates
  pattern/      *.md   ← (usually empty — disposition collects at the global level)
  decision/     *.md   ← this project's decisions (why this arc, why this audience framing)
  reference/    *.md   ← this project's pointers to external resources (brand guide, accessibility rubric)
```

- One file = one topic (e.g. `convention/defense-defect-patterns.md`). Filenames are
  **English-keyword slugs even when the topic is Korean** (paraphrase to English keywords —
  KN-4). When writing via code, use `query_helper.title_to_slug()` — it owns the deterministic
  hash fallback; never improvise a hash inline. Validate the target with
  `query_helper.safe_wiki_path()` before any Write into `.omd/wiki/**` (KN-3).
- Each file is free-form human-readable .md. No machine-parse schema (grep only).
- `category` maps 1:1 to the sub-directory names (local: `convention`·`pattern`·`decision`·`reference`; global: `convention`·`pattern`·`decision`).
- ⚠️ `.omd/wiki/` is *project-wide* accrual, so it lives **outside** the per-job `.omd/<slug>/` (output-layout) — it is not tied to a slug and survives across sessions/jobs.
- ⚠️ **Only "document-agnostic reusable form assets" rise to global** (org/lab style-spec, disposition, reusable decisions). Project-specific knowledge (this deck's defect quirks) stays local, and ⚠️ **a document's content (text, claims, numbers, sources) is *permanently forbidden* from rising to global** (the content-preservation invariant — `learning-protocol.md` §6.F, the omd analogue of oms's citation-safety). This is how the "never to a distributed/user-scope config" anti-pattern is reconciled — the global level is *the parent folder's `.omd/`* (still work-root-relative), not a distributed config, and only form assets cross up.
- ⚠️ **Cross-project confidentiality gate (omd-specific, no oms analogue).** The global level is *shared by multiple document projects* — and a workspace may hold confidential company material. A global-eligible note must carry only the **abstracted form rule** ("captions are 12pt black"), never a **project-identifiable** detail (client name, internal codename, a confidential path). A rule like "the ACME deck uses red captions" stays **local** — promoting it to global would leak it into an unrelated (personal/external) project's session via ascent. Form abstracts; identifiers stay local. (`learning-protocol.md` §1.4 / §6.F.)

> ⚠️ The global-only `history/` category that the sibling oms harness carries (for its `init` to relate/dedup new *papers*) is **intentionally not present** in omd — omd has no `init` stage and no document-dedup need, so it would be a dead category here.

### ⭐ `convention/` vs `pattern/` — heavy-channel candidates come from convention only (2026-05-31 H6 backport)

The split is load-bearing (`references/learning-protocol.md` §1):
- **`convention/`** = *how the output looks* (caption style, layout, reject reasons). When observed
  repeatedly it escalates to `learned.md` and becomes a **heavy-channel promotion candidate** (can
  harden into a style-spec default).
- **`pattern/`** = *how the user works* (disposition, working style, preferences). **Light only —
  never promoted.** Disposition is not enforceable; it is a note every stage *reads* to match tone
  and verbosity. A `pattern/` note never rises into `learned.md`.

### ⭐ confidence frontmatter — repeated sighting raises trust (OMC backport, H6)

Each wiki note carries frontmatter `confidence: high | med | low`. Re-observing the same pattern
climbs `low → med → high`, and a merge **keeps the higher** value (a weak re-sighting never
demotes). This repetition-climb is the light-channel analogue of omp's `evidence_count`, and the
signal that links to the heavy gate: a `convention/` note reaching **`confidence: high`** means its
`OBS` likely approached `evidence_count ≥ 3` — worth a `docs-learn` look. confidence is a
qualitative 3-level grade (+ sighting count) only — **no numeric weighted sum, no threshold magic**.
Example:

```markdown
---
confidence: high
sightings: 3
---
# defense-deck defect patterns
## 2026-05-27 — grey captions flagged repeatedly (3rd sighting → high)
...
```

### actionable status — a recorded correction must not silently stall (family wiki-status convention)

A note may carry an optional frontmatter `status: needs-revision | resolved` (plus `blocked-on: <free text>`
while open). `needs-revision` marks a measured style/spec correction that is **recorded but not yet
applied**; `resolved` is terminal (say why in a dated body section — the note is never deleted).
**Absent = not actionable** (every existing note). This closes the family failure mode where an
actionable finding is archived in the wiki yet silently dropped before the next build/promotion.

- **Enumeration is deterministic grep** (omd's "grep only" contract, no schema): `grep -rlE
  '^status:[[:space:]]*needs-revision[[:space:]]*$' .omd/wiki/` lists every open correction
  keyword-independently (anchored `$` so it matches the linter's exact-token semantics, not
  `needs-revision-old`). When
  `python3` is available, `references/wiki/lint_wiki.py` also surfaces each as an `open-revision`
  warning, and flags a mistyped value as `unknown-status` (a typo would silently leave the
  enumeration). The on-disk `status:`/`blocked-on:` key names are identical across every om* harness
  (the value vocabulary is per-harness: omx `needs-experiment`/`needs-apply-before-retrain`/
  `resolved`, omd `needs-revision`/`resolved`, oms `open-gap`/`resolved`), so the
  key-anchored grep shape is family-wide.
- **Carry-forward boundary**: `docs-verify` and `docs-learn` run this enumeration before a build /
  style-promotion and name any open `needs-revision` note as a warning finding — so a measured
  correction cannot be built over unknowingly. WARN only (omd never hard-gates on the wiki).

---

## `wiki_query(category)` abstract-function contract

```
wiki_query(category) → list of matched .md excerpts (empty list if none)
```

- **Current implementation (two-level ascent merge)**:
  ```
  local_hits  = grep(<cwd>/.omd/wiki/<category>/, keywords)              # local — this document project
  parent_omd  = ascent(<cwd>): cwd→parent, the first .omd/ excluding self  # git's .git-lookup
  global_hits = grep(parent_omd/wiki/<category>/, keywords) if parent_omd else []  # global — user/org reuse
  return merge(local_hits, global_hits)   # provenance-tagged [wiki:local] / [wiki:global]
  ```
  Deterministic grep only (keyword matching, incl. CJK bi-gram — implemented by
  `references/wiki/query_helper.py`; shell out `python3 <plugin>/references/wiki/query_helper.py
  match <category-dir> "<query>"` when python3 is available, plain grep as the degrade path).
  ⚠️ `ascent` never climbs above the user's home directory (ST-3) — same hard lower bound
  as the layout diagram above.
  The caller (inspector) greps by presentation-type / disposition keywords to pull relevant excerpts. category for the local level is one of the four (`convention`·`pattern`·`decision`·`reference`); the global level carries `convention`·`pattern`·`decision` (no `history` — see layout above). (Either level — missing directory → that level is an empty list; a fresh project starts from an empty store.)
- **Caller/implementation boundary (future swap point)**: the inspector calls an *abstract function* `wiki_query`; it does not know whether the implementation is "two-level grep" or a standalone MCP. **The ascent, the merge, and the provenance-tagging are all sealed inside this function** — the call site (inspector pre-commitment) does not change by a single line. If a standalone wiki MCP is later adopted, swap only this function's implementation.
- **Graceful degrade on absence**: if either the local or the global level is empty, or there is no ancestor `.omd/`, that level returns an empty list — not an error. The inspector proceeds on what exists (or on its own prediction).

---

## Data this store *newly* collects (net-new — not a migration)

Defect patterns and induced style specs are **net-new data**. docs-standardize today induces a style spec into *session-volatile* state that evaporates; this wiki is where that becomes a durable "lab standard." Likewise recurring defect patterns per type are collected *fresh* by inspector sessions — not migrated from any existing card.

Accrual is **automatic** — docs-pilot's wiki-capture step does it (after verify, before terminal — `docs-pilot/SKILL.md` Step 7): when a reusable spec or a recurring defect pattern surfaces in inspect/verify/standardize, it appends a line to `convention/<topic>.md`. A standalone single-stage run may also append directly. **Automatic is the default** — this is the write half of the two-way loop above. Skip on user `--no-wiki`. Append-only, grep-checks for duplicates first, passes through on an empty session, never accrues a guess (only what was actually surfaced).

---

## ⚠️ Safety boundary (deterministic only)

- **wiki content is a *secondary memo* — never a primary source.** It informs prediction; it is not the source of truth for the artifact. The inspector tags wiki excerpts as `[wiki]` to distinguish them from its own prediction (`[own]`).
- **Lookup is deterministic keyword matching only — embedding search is permanently forbidden.** grep (current) or a future MCP must both use deterministic matching. (Mirrors the OMS citation-safety invariant: no embedding similarity search, now or ever.)
- ⚠️ **No light→enforce shortcut** (H6 backport, `learning-protocol.md` §6.D): a wiki note (even at `confidence: high`) is *advice*, not an enforced default. To harden it into a style-spec default it MUST travel the heavy channel via `learned.md` and pass the **human gate**. No confidence is high enough for a wiki note to change a style-spec default directly. In particular `pattern/` (disposition) is permanently light — never a promotion target.
- ⚠️ **Content-preservation (omd-specific, `learning-protocol.md` §6.F):** the wiki and the heavy channel learn **form, never content**. A document's text/claims/numbers/sources never become a wiki note's enforceable default nor a `learned.md` promotion target — only style/layout/structure. This is the omd analogue of OMS's citation-safety.
