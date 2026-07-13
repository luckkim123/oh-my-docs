# Design principles

## Cards are the single source of truth

Each format's tools, traps, and formula knowledge lives in its own knowledge card
under `references/formats/` — the single source of truth that OMD's builder and
verifier agents read, instead of wrapping existing skills. A card is a data file, not
a skill; duplicating its knowledge into an agent file is avoided on purpose, so there
is exactly one place to update when a tool version or a trap changes.

## Inspect and verify are separate lanes — no self-approval

`docs-inspect` (formative) and `docs-verify` (summative) are deliberately separate
lanes. The agent that critiques a draft is not the agent that grants the pass — a
structural guard against self-approval.

## Fail-open, advisory hooks

Hooks are stdlib-only and fail-open: a hook that errors returns success, so the
session is never blocked. Reminders nudge toward the right next step; they do not
force a fix before continuing.

## Artifact-set layout

Single-file formats keep `outputs/<slug>/current.<ext>` as the one deliverable.
Multi-file genres (repo-docs, site) use `outputs/<slug>/current/` — a whole
directory — paired with `.omd/<slug>/manifest.json`. Either way, the invariant holds:
the user-visible entry point is exactly one current entry, one file or one directory,
never both, never siblings. `outputs/` is the "display shelf" the user sees; `.omd/`
is the workbench — version copies, renders, and other intermediates that would
otherwise bloat the output folder.
