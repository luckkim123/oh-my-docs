# references/notepad.md — `.omd/notepad.md` 3-tier contract (G2)

`.omd/notepad.md` is the work-root scratch memory that survives compaction. Three
fixed sections (exact headings — the hook greps them):

| Section | Writer | Pruning | Purpose |
|:--|:--|:--|:--|
| `## Priority Context` | docs-pilot on entry (pipeline-critical constraints: original-destruction ban, single `current.<ext>` invariant, current gate + slug) | **never pruned** | reinjected verbatim after compaction (SessionStart source=compact → additionalContext) |
| `## Working Notes` | any stage, freely | hook trims to the newest 40 lines when the file exceeds 16KiB (PreCompact, atomic ST-1) | session-scoped scratch |
| `## Manual` | the user only | **never touched by any tool** | user-owned notes |

- .md is the default and sufficient; a notepad MCP is an optional mirror, never required
  (docs-pilot Execution_Policy).
- The hook (`hooks/precompact_reinject.py`) is advisory infrastructure: fail-open, never
  blocks, never rewrites Priority/Manual, and prunes only when oversized.
- This file is the omd adaptation of OMC's notepad 3-tier (Priority/Working/Manual);
  the .md-degrade philosophy comes from `references/omc-backport-analysis.md` T11.
