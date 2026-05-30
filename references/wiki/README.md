# references/wiki — accumulated secondary-memo store (specializes the more you use it)

This store **compounds session-volatile data into a "lab standard"** persistent memo. It runs as a **two-way loop**:
- **Write (automatic)**: docs-pilot's wiki-capture step **auto-appends** the defect patterns / induced style specs / decisions that inspect/verify/standardize surfaced this session (no approval — the light channel, `docs-pilot/SKILL.md` Step 7).
- **Read (automatic)**: the next session's doc-inspector pre-commitment pulls those accumulated patterns via `wiki_query(category)`.

Write and read close the loop, so **the harness specializes to this presentation type / this org's standard the more it is used** — without the user ever explicitly saying "learn this." Ships empty (generic); diverges as it operates.

It is the current backing for the `wiki_query(category)` abstract function, and nothing breaks when it is empty or absent (the inspector proceeds on its own prediction).

---

## Directory layout

⚠️ **The data accrues in the work area (`.omd/wiki/`) — NOT in this plugin repo.** This README is the *contract*, so it ships inside the plugin (`references/wiki/README.md`), but the accumulated data is written to **`.omd/wiki/` under the target project root** (`.omd/` is gitignored — it never dirties the plugin/distributable and diverges per project, which is what makes "specializes to *this* project" hold). Same pattern as OMC's `.omc/wiki/` (project-local).

```
<project root>/.omd/wiki/          ← work area, gitignored, diverges per project (carries across sessions)
  convention/   *.md   ← per-type defect patterns + induced style specs (inspector reads this) — ⭐ source of heavy-channel candidates
  pattern/      *.md   ← ⭐NEW: how the user *works* (disposition) — light only, never promoted
    work-profile.md      ← what they mostly do / which deck types ("you mostly make defense decks, reports")
    working-style.md     ← how they work (reviews closing slide first, prefers diagram-heavy)
    preferences.md       ← tone/verbosity preferences (dislikes verbose, prefers direct)
  decision/     *.md   ← past decisions (why this arc, why this audience framing, what worked well)
  reference/    *.md   ← pointers to external resources (brand guide, accessibility rubric)
```

- One file = one topic (e.g. `convention/defense-defect-patterns.md`, `convention/lab-style-spec.md`).
- Each file is free-form human-readable .md. No machine-parse schema (grep only).
- `category` maps 1:1 to the **four** sub-directory names above.
- ⚠️ `.omd/wiki/` is *project-wide* accrual, so it lives **outside** the per-job `.omd/<slug>/` (output-layout) — it is not tied to a slug and survives across sessions/jobs.

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

---

## `wiki_query(category)` abstract-function contract

```
wiki_query(category) → list of matched .md excerpts (empty list if none)
```

- **Current implementation**: **deterministic grep** (keyword matching, incl. CJK bi-gram) over the target project's `.omd/wiki/<category>/`. The caller (inspector) greps by presentation-type / disposition keywords to pull relevant excerpts. category is one of the four (`convention`·`pattern`·`decision`·`reference`). (Missing directory → empty list — a fresh project starts from an empty store.)
- **Caller/implementation boundary (future swap point)**: the inspector calls an *abstract function* `wiki_query`; it does not know whether the implementation is grep or a standalone MCP. If a standalone wiki MCP is later adopted, **swap only this function's implementation** (grep → MCP) — the call sites (inspector pre-commitment) do not change.
- **Graceful degrade on absence**: if the store is empty or the directory is missing, return an empty list — not an error. The inspector proceeds on its own prediction.

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
