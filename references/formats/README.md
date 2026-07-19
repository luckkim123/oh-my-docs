# Format Cards — authoring contract

> Data files, not skills. Every card is the single source of truth for one format's
> tools, traps, and verified techniques. Agents (`doc-builder`, `doc-verifier`,
> `doc-inspector`) read the card; they never duplicate its knowledge.

## Required sections (every card)

The three sections all five existing cards share — new cards (repo-docs, site, …)
must carry them too; everything else is format-specific and free-form:

1. **`## Engine`** — the borrowed tools, one table row per tool, each row pinning the
   **measured version** (e.g. `python-pptx` 1.0.2) and its verification status on this
   machine. A row without a version number is not a pin.
2. **Hard traps** — API/format traps with `[VERIFIED ✓ — date]`-stamped evidence. Genre cards (repo-docs, site) whose traps cite external standards rather than machine measurements carry `[source: <standard> — accessed YYYY-MM-DD]` markers instead — a standards citation is not a machine measurement, and stamping it VERIFIED would be dishonest.
3. **Version-snapshot policy** — how `.omd/<slug>/versions/` snapshots work for this format.

Conditional: a `License_Note` section whenever material is borrowed from an external
source (anthropics/skills convention).

## VERIFIED stamp grammar

New stamps carry the engine and version whenever the claim is engine-dependent:

    [VERIFIED ✓ — YYYY-MM-DD, <engine> <version>]     e.g. [VERIFIED ✓ — 2026-06-16, python-pptx 1.0.2]

Legacy stamps (date-only, or `this machine`) are grandfathered — normalize them only
when the surrounding section is next re-verified (R5+ sweep; do not bulk-rewrite).

## Engine-drift demotion rule (G7)

At build/verify time the agent measures the live engine version (e.g.
`python3 -c "import pptx; print(pptx.__version__)"`; `soffice --version`) and compares it
against the card's `## Engine` pins. On mismatch, every VERIFIED claim tied to that
engine is treated as **`UNVERIFIED (engine drift)`** for this run — state the demotion
in the report (builder: Build Notes; verifier: Verification Report), then either
re-verify the claim live or proceed with the honest UNVERIFIED label. Never silently
trust a stamp measured on a different engine version. (Same family as the D3 rule:
a missing engine yields `UNVERIFIED (engine unavailable)`, never a silent PASS.)

Canonical implementation: `references/snippets/engine_check.py::parse_engine_pins` /
`live_version` / `check_engine_drift`.
