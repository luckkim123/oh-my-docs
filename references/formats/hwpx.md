# Format Knowledge Card — hwpx  `[STATUS: STUB — needs python-hwpx research before full card]`

> Data file for OMD agents. The Korean office format. MVP pilots pptx; this is a placeholder.

## Format reality (from 2026-05-27 research)
- **`.hwpx`** (newer, OWPML = ZIP+XML) — readable / writable / editable on macOS via **`python-hwpx`**
  (pure Python, cross-platform). This is the **default path**.
- **`.hwp`** (older v5 binary) — **cannot be written in pure Python on macOS** (needs Windows + Hancom
  COM automation). Handle `.hwp` input only as a **normalize-to-hwpx/docx conversion gate**, never
  direct write.

## Engine (planned)
| Tool | Role | Status |
|:---|:---|:---|
| `python-hwpx` | read/write/edit .hwpx | NOT installed — research support scope first |
| soffice | .hwpx render? | uncertain — verify before relying |

## Formulas — OPEN QUESTION
Hancom equation (HML equation objects). python-hwpx support scope is **unresearched**. Must
investigate before writing the formula section. Do not guess.

## Version-snapshot policy
Same layout as the pptx card: the one delivered `outputs/<slug>/current.hwpx`, with version
snapshots and renders in the `.omd/<slug>/` work area (`versions/`, `renders/`, `tmp/`). See
`references/output-layout.md` for the fixed structure and naming.
