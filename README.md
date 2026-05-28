# oh-my-docs (OMD)

A document-work harness for Claude Code — the OMC architecture (stage skills + role agents +
routing hook + manifest) ported to the *document* domain. **Borrow the engine, build the brain**:
OMD drives python-pptx / soffice / matplotlib but owns its own gates, verification, intake, and
formula handling rather than wrapping existing skills.

One of the specialized harnesses the omha meta-coordinator routes document tasks to (omha picks the
*lane*; OMD picks *format + stage* within the document lane). OMD is standalone — it installs and
runs without omha.

## Structure (stage-centric)

```
skills/   docs-intake · docs-standardize · docs-plan · docs-build · docs-inspect · docs-verify · docs-pilot
agents/   doc-analyzer · doc-planner · doc-builder · doc-inspector · doc-verifier   (OMC XML 7-section)
references/formats/{pptx,docx,hwpx}.md   format tools/traps/formula knowledge (single source of truth)
references/rubrics/ppteval.md            Content/Design/Coherence (inspect + verify)
hooks/route_emit.py                      UserPromptSubmit format/stage routing checkpoint (stdlib only)
hooks/docs_verify_emit.py                PostToolUse — after a Bash document build/convert, a
                                         freeze-safe docs-verify reminder (stdlib only, fail-open)
```

Skills are thin scores; agents are the brains they dispatch (`Task(subagent_type="oh-my-docs:doc-*")`).
`docs-inspect` (formative) and `docs-verify` (summative) are deliberately separate lanes — no
self-approval (doc-verifier carries the triple ban: read-only tools + separate-pass constraint +
Role NOT-responsible for authoring). Agents that hit uncovered SDK behavior consult external docs
(`<External_Consultation>`: format card → Context7 → official docs) rather than guessing.
`docs-pilot` orchestrates the full brief→document flow with a user gate at each step.

## Status (2026-05-28)

MVP: **pptx pilot**. Skills, agents, format cards, and routing hook are implemented and structurally
verified. Formula rendering proven (matplotlib-image path VERIFIED via soffice; native OMML path is
PowerPoint-only). docx/hwpx are stub cards — build logic clones after the pptx pilot is validated
end-to-end in a live session.

Design: `/Users/kimseungmin/Desktop/workspace/00-09_Meta/02_Decisions/2026-05-28-oh-my-docs-redesign-stage-centric.md`

## Prerequisites

python-pptx, LibreOffice (soffice), pdftoppm (poppler), matplotlib + Pillow. macOS / Windows
document environments (Linux is skipped — not a document-authoring target).
