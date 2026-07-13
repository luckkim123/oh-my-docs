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
skills/   docs-intake · docs-standardize · docs-plan · docs-build · docs-inspect · docs-verify
          docs-convert · docs-revise · docs-translate · docs-pilot · docs-learn · docs-pdf
agents/   doc-analyzer · doc-planner · doc-builder · doc-inspector · doc-verifier   (OMC XML 7-section)
references/formats/{pptx,docx,xlsx,hwpx}.md   format tools/traps/formula knowledge (single source of truth)
references/formats/pdf.md                     pdf as *input/convert layer* (not a generation format)
references/rubrics/ppteval.md                 Content/Design/Coherence (inspect + verify)
references/themes/                            10 fallback font/color presets (no-reference branch)
references/wiki/README.md                     two-level wiki contract (local + global ascent)
hooks/route_emit.py                           UserPromptSubmit format/stage routing checkpoint (stdlib only)
hooks/docs_verify_emit.py                     PostToolUse — after a Bash document build/convert, a
                                              freeze-safe docs-verify reminder (stdlib only, fail-open)
```

Skills are thin scores; agents are the brains they dispatch (`Task(subagent_type="oh-my-docs:doc-*")`).
`docs-inspect` (formative) and `docs-verify` (summative) are deliberately separate lanes — no
self-approval (doc-verifier carries the triple ban: read-only tools + separate-pass constraint +
Role NOT-responsible for authoring). Agents that hit uncovered SDK behavior consult external docs
(`<External_Consultation>`: format card → Context7 → official docs) rather than guessing.
`docs-pilot` orchestrates the full brief→document flow with a user gate at each step.

## Status (2026-07-13)

**v0.1.0 (R1 — hygiene + core gates).** All four office format cards are complete
(**pptx, docx, xlsx, hwpx**), plus a pdf *input-side* card (`docs-pdf` skill) and a two-level
wiki (local + global ascent). 12 skills · 5 agents · hooks with regression tests
(`python3 -m pytest tests/`). Formula rendering proven by real soffice renders: **docx** native
OMML path VERIFIED (editable math, with two documented soffice caveats — `\hat` accent,
`\sum`/`\,` tofu box) plus matplotlib-image fallback; **pptx** is matplotlib-image only
(soffice/Impress renders native OMML blank). The pptx path is validated end-to-end in live
sessions; docx/xlsx/hwpx build paths follow their cards.

Roadmap: R1 hygiene+gates (this release) → R2 repo-docs genre → R3 MkDocs site genre →
R4 knowledge lifecycle — see `docs/superpowers/specs/2026-07-11-omd-program-design.md`.

Design: the stage-centric redesign decision doc (maintained in the author's planning notes, outside this repo).

## Prerequisites

python-pptx, **python-docx**, **python-hwpx**, LibreOffice (soffice), pdftoppm (poppler), matplotlib + Pillow.

```sh
# Python packages (all platforms)
pip install python-pptx python-docx python-hwpx matplotlib Pillow
```

LibreOffice (`soffice`) and poppler (`pdftoppm`) are the only native dependencies — install via your
platform's package manager:

```sh
# macOS (Homebrew)
brew install --cask libreoffice && brew install poppler

# Debian/Ubuntu
sudo apt install libreoffice poppler-utils

# Fedora/RHEL
sudo dnf install libreoffice poppler-utils

# Windows (winget; or choco install libreoffice poppler)
winget install TheDocumentFoundation.LibreOffice
```

The runtime itself is cross-platform (the format cards and cleanup logic branch macOS/Linux/Windows).
`.hwpx` is fully in-process via python-hwpx on every platform; the one exception is the **`.hwp`
binary** (older v5 OLE) — it cannot be written in pure Python and is a normalize-to-hwpx/docx
conversion gate only (see `references/formats/hwpx.md`).

(python-docx is wired and the docx format card is complete; the build path is exercised after the
pptx pilot ships end-to-end. python-hwpx is wired and the hwpx format card is complete — form-fill is
the main use case, math is unsupported/v2. xlsx uses openpyxl/xlsxwriter — `pip install openpyxl
xlsxwriter` when building spreadsheets.)
