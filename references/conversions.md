# Conversion Reference — format / delivery transforms

> Data file for docs-convert. Which conversions are proven, which are gated, which are unavailable.
> Borrow the engine (soffice / pandoc / python-hwpx); never hand-roll a converter that exists.

## Conversion matrix (status as of 2026-05-28)

| From → To | Tool | Status | Note |
|:---|:---|:---|:---|
| .pptx → .pdf | `soffice --headless --convert-to pdf` | **VERIFIED ✓** | delivery PDF; probed, 12 KB out, exit 0 |
| .docx → .pdf | `soffice --headless --convert-to pdf` | likely (same engine) | verify on first real use |
| .md → .docx | `pandoc` | UNVERIFIED | check `pandoc` installed first |
| .hwp (v5 binary) → .hwpx/.docx | — | **GATE — not pure-Python on macOS** | needs Windows + Hancom COM, or a manual export. Do NOT attempt direct write |
| .hwpx → .pdf | soffice? | UNVERIFIED | python-hwpx NOT installed (2026-05-28); research before relying |

## Rules
- **soffice conversions are the proven path** (.pptx/.docx → .pdf). Use `--outdir`, check exit 0,
  and confirm the output file exists + non-trivial size before claiming success.
- **.hwp input is a conversion GATE, not a build path**: normalize to hwpx/docx (manual export on
  macOS) before any OMD stage touches it. Direct .hwp write is out of scope (see hwpx card).
- A row is `VERIFIED ✓` only after an actual conversion ran and the output was confirmed. No guessing.
- Conversion never mutates the source — write to outputs/<slug>/ with a new extension (a delivery
  conversion is a separate output family from the build's `current.<ext>`; it shares the folder but
  does not overwrite `current.<ext>`). See references/output-layout.md for the folder convention.
