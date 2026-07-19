# oh-my-docs (OMD)

Multi-agent orchestration harness specialized for document work (pptx/docx/xlsx/hwpx).

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

## Install

A Claude Code plugin (`.claude-plugin/plugin.json`) — install it the way your Claude Code
setup adds plugins. It runs standalone; no other harness is required.

Prerequisites — the Python/native tools the format cards drive:

```sh
# Python packages (all platforms)
pip install python-pptx python-docx python-hwpx matplotlib Pillow openpyxl xlsxwriter
```

LibreOffice (`soffice`) and poppler (`pdftoppm`) are the only native dependencies:

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

`.hwpx` is fully in-process via python-hwpx on every platform; the one exception is the
**`.hwp` binary** (older v5 OLE) — it cannot be written in pure Python and is a
normalize-to-hwpx/docx conversion gate only (see `references/formats/hwpx.md`).

## Usage

Stage pipeline — skills are thin scores, agents are the brains they dispatch
(`Task(subagent_type="oh-my-docs:doc-*")`):

```text
docs-intake · docs-standardize · docs-plan · docs-build · docs-inspect · docs-verify
docs-revise · docs-convert · docs-translate
```

`docs-inspect` (formative) and `docs-verify` (summative) are deliberately separate lanes —
no self-approval. `docs-pilot` orchestrates the full brief→document flow with a user gate
at each step. Meta skills: `docs-learn` (wiki promotion), `docs-pdf` (pdf as input/convert
layer, never a generation format).

**Formats**: pptx / docx / xlsx / hwpx (office, render-capable) and the text genres
**repo-docs** (README/CHANGELOG/community-health set) and **site** (MkDocs + Material
static docs site). Each format's tools/traps/formula knowledge lives in its own card under
`references/formats/` — the single source of truth OMD's builder and verifier agents read
instead of wrapping existing skills.

**Status**: R1 v0.1.0 shipped the four office format cards + core verify/hygiene gates.
R2 v0.2.0 adds the repo-docs genre — card-delegated gates generalized across the builder/
verifier/inspect/standardize/revise skill pair, an artifact-set output layout (multi-file
deliverables with a manifest), and this README/CHANGELOG regenerated through that pipeline
(dogfooding).
R3 v0.3.0 adds the site genre — MkDocs + Material card with machine-measured engine
stamps, `mkdocs build --strict` as the deterministic gate, Diátaxis structure frames, and
omd's own docs site built as the E2E pilot (fixture-pinned dogfood guard).
R4 v0.4.0 closes the knowledge lifecycle — CJK/English wiki write and query guards,
report-only wiki lint feeding `docs-learn`, a notepad contract that survives context
compaction, stop-guard and ownership gates over pilot runs, and the observing-stage
capture-then-curate loop. This completes the R1–R4 release train.

## Architecture

The OMC architecture (stage skills + role agents + routing hook + manifest) is ported to
the document domain.

```text
skills/       docs-intake · docs-standardize · docs-plan · docs-build · docs-inspect ·
              docs-verify · docs-convert · docs-revise · docs-translate · docs-pilot ·
              docs-learn · docs-pdf
agents/       doc-analyzer · doc-planner · doc-builder · doc-inspector · doc-verifier
references/   formats/ (pptx, docx, xlsx, hwpx, pdf, repo-docs, site) · rubrics/ (ppteval,
              repo-docs-rubric, site-rubric) · themes/ (10 office fallback presets) · wiki/ ·
              output-layout.md · learning-protocol.md
hooks/        docs_route_emit.py (UserPromptSubmit routing) · docs_verify_emit.py
              (PostToolUse verify reminder, Bash + Edit|Write) · docs_stop_guard.py ·
              docs_model_guard.py
```

Two-level wiki (local `.omd/wiki/` + global ascent, `references/wiki/README.md`) lets each
project's document work specialize over time — the global level carries a permanent ban on
document content (text, claims, numbers, sources), local-only. Design and release history:
`docs/superpowers/specs/` and `docs/superpowers/plans/`.

## Contributing

```sh
python3 -m pytest tests/ -q
```

Invariants worth knowing before sending a change: hooks are stdlib-only and fail-open;
`tests/test_distribution_axiom.py` checks that shipped files never carry personal home
paths or emails. See `docs/superpowers/specs/` and `docs/superpowers/plans/` for the
design docs and TDD plans behind each release.

## License

MIT
