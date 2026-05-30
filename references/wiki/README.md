# references/wiki — accumulated secondary-memo store (carries across sessions)

Where doc-inspector's pre-commitment (predicting common defects before reading the renders) pulls *patterns accumulated by previous sessions*. This store **compounds session-volatile data into a "lab standard"** persistent memo — e.g. the induced style spec (fonts, colors, margins) from docs-standardize, or recurring defect patterns per presentation type.

It is the current backing for the `wiki_query(category)` abstract function, and nothing breaks when it is empty or absent (the inspector proceeds on its own prediction).

---

## Directory layout

```
references/wiki/
  convention/   *.md   ← per-type defect patterns + induced style specs (inspector reads this)
  decision/     *.md   ← past decisions (why this arc, why this audience framing)
  reference/    *.md   ← pointers to external resources (brand guide, accessibility rubric)
```

- One file = one topic (e.g. `convention/defense-defect-patterns.md`, `convention/lab-style-spec.md`).
- Each file is free-form human-readable .md. No machine-parse schema (grep only).
- `category` maps 1:1 to the three sub-directory names above.

---

## `wiki_query(category)` abstract-function contract

```
wiki_query(category) → list of matched .md excerpts (empty list if none)
```

- **Current implementation**: **deterministic grep** (keyword matching) over `references/wiki/<category>/`. The caller (inspector) greps by presentation-type keywords to pull relevant excerpts.
- **Caller/implementation boundary (future swap point)**: the inspector calls an *abstract function* `wiki_query`; it does not know whether the implementation is grep or a standalone MCP. If a standalone wiki MCP is later adopted, **swap only this function's implementation** (grep → MCP) — the call sites (inspector pre-commitment) do not change.
- **Graceful degrade on absence**: if the store is empty or the directory is missing, return an empty list — not an error. The inspector proceeds on its own prediction.

---

## Data this store *newly* collects (net-new — not a migration)

Defect patterns and induced style specs are **net-new data**. docs-standardize today induces a style spec into *session-volatile* state that evaporates; this wiki is where that becomes a durable "lab standard." Likewise recurring defect patterns per type are collected *fresh* by inspector sessions — not migrated from any existing card.

Accrual is by the person/session that ran standardize or inspect: when a reusable spec or a recurring defect pattern surfaces, append a line to `convention/<topic>.md`. (Accrual is optional, not forced.)

---

## ⚠️ Safety boundary (deterministic only)

- **wiki content is a *secondary memo* — never a primary source.** It informs prediction; it is not the source of truth for the artifact. The inspector tags wiki excerpts as `[wiki]` to distinguish them from its own prediction (`[own]`).
- **Lookup is deterministic keyword matching only — embedding search is permanently forbidden.** grep (current) or a future MCP must both use deterministic matching. (Mirrors the OMS citation-safety invariant: no embedding similarity search, now or ever.)
