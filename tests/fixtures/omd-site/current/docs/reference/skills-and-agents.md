# Skills and agents

oh-my-docs ports the OMC architecture (stage skills + role agents) to the document
domain: skills are thin scores, agents are the brains they dispatch via
`Task(subagent_type="oh-my-docs:doc-*")`.

## Skills (12)

| Skill | Role |
| --- | --- |
| `docs-intake` | Stage pipeline — first stage, brief intake. |
| `docs-standardize` | Stage pipeline — standardize stage. |
| `docs-plan` | Stage pipeline — plan stage. |
| `docs-build` | Stage pipeline — build stage. |
| `docs-inspect` | Formative lane — improvement points, not a verdict; separate from `docs-verify`, no self-approval. |
| `docs-verify` | Summative lane — the deterministic gate; separate from `docs-inspect`, no self-approval. |
| `docs-convert` | Stage pipeline — convert stage. |
| `docs-revise` | Stage pipeline — revise stage. |
| `docs-translate` | Stage pipeline — translate stage. |
| `docs-pilot` | Orchestrates the full brief-to-document flow with a user gate at each step. |
| `docs-learn` | Meta skill — wiki promotion. |
| `docs-pdf` | Meta skill — pdf as an input/convert layer, never a generation format. |

## Agents (5)

| Agent | Role |
| --- | --- |
| `doc-analyzer` | Reads existing material within a bounded input whitelist (README/CHANGELOG/community-health files, package manifests, a structure-only Grep/Glob scan, a recent commit-log summary) — never the whole codebase. |
| `doc-planner` | Designs the document's structure/outline — e.g. it consumes a genre's structure frame (such as the site genre's Diátaxis quadrant grid) to plan the layout. |
| `doc-builder` | Reads the target format's knowledge card (tools, traps, verified techniques) and produces the artifact through the card's borrowed engine. |
| `doc-inspector` | Runs the formative lane (`docs-inspect`). |
| `doc-verifier` | Runs the summative lane (`docs-verify`) — the deterministic, exit-code-first gate each format/genre card defines. |
