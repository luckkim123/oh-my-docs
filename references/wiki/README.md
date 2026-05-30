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
  convention/   *.md   ← per-type defect patterns + induced style specs (inspector reads this)
  decision/     *.md   ← past decisions (why this arc, why this audience framing)
  reference/    *.md   ← pointers to external resources (brand guide, accessibility rubric)
```

- One file = one topic (e.g. `convention/defense-defect-patterns.md`, `convention/lab-style-spec.md`).
- Each file is free-form human-readable .md. No machine-parse schema (grep only).
- `category` maps 1:1 to the three sub-directory names above.
- ⚠️ `.omd/wiki/` is *project-wide* accrual, so it lives **outside** the per-job `.omd/<slug>/` (output-layout) — it is not tied to a slug and survives across sessions/jobs.

---

## `wiki_query(category)` abstract-function contract

```
wiki_query(category) → list of matched .md excerpts (empty list if none)
```

- **Current implementation**: **deterministic grep** (keyword matching) over the target project's `.omd/wiki/<category>/`. The caller (inspector) greps by presentation-type keywords to pull relevant excerpts. (Missing directory → empty list — a fresh project starts from an empty store.)
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
