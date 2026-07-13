# Getting started

## Install

oh-my-docs is a Claude Code plugin (`.claude-plugin/plugin.json`). Install it the way
your Claude Code setup adds plugins — it runs standalone, no other harness required.

Prerequisites — the Python/native tools the format cards drive:

```sh
pip install python-pptx python-docx python-hwpx matplotlib Pillow openpyxl xlsxwriter
```

LibreOffice (`soffice`) and poppler (`pdftoppm`) are the only native dependencies:

```sh
# macOS (Homebrew)
brew install --cask libreoffice && brew install poppler
```

`.hwpx` is fully in-process via python-hwpx on every platform; the one exception is the
`.hwp` binary (older v5 OLE) — it cannot be written in pure Python and is a
normalize-to-hwpx/docx conversion gate only.

## Your first pipeline: intake to verify

oh-my-docs runs document work as a stage pipeline. Skills are thin scores; agents are
the brains they dispatch (`Task(subagent_type="oh-my-docs:doc-*")`).

1. **docs-intake** — gather the brief and reference material.
2. **docs-plan** — design the structure/outline before any content is built.
3. **docs-build** — produce the artifact from the approved plan.
4. **docs-verify** — the summative gate. `docs-inspect` (formative) and `docs-verify`
   (summative) are deliberately separate lanes — no self-approval.

`docs-pilot` orchestrates this full brief-to-document flow with a user gate at each
step, if you would rather not drive each stage yourself.
