# Format Knowledge Card — xlsx

> **What this is**: A data file, not a skill. The OMD agents (`doc-builder`, `doc-verifier`,
> `doc-inspector`) read this card to know the tools, traps, and verified techniques for the
> `.xlsx` format. Borrow the engine (openpyxl / xlsxwriter / soffice); the orchestration brain
> lives in the agents and stage skills. Sibling cards: `pptx.md`, `docx.md` (same discipline;
> xlsx differs most in its **verify gate** — spreadsheets don't proofread by "read every page").

## Engine — two libraries, explicit routing

| Tool | Role | Verified on this machine (2026-05-31) |
|:---|:---|:---|
| `openpyxl` 3.1.5 | **read + edit existing** files; charts, conditional formatting, pivots (read) | ✓ installed |
| `xlsxwriter` 3.2.9 | **new-file create / bulk write** (write-only); best chart fidelity | ✓ installed |
| `soffice` (LibreOffice) | formula **recalculation** (macro) + optional render | resolve on PATH |
| `pandas` | dataframe → sheet convenience (backend = openpyxl/xlsxwriter) | optional |

**Routing rule (load-bearing):**
- **New file, bulk write, charts** → `xlsxwriter` (faster, better charts). **Cannot read or edit
  existing files** (write-only).
- **Existing file, read or modify** → `openpyxl`. ⚠️ **openpyxl `load()` of an existing file can
  DROP chart objects** (known limitation) — round-tripping a chart-bearing file via openpyxl loses
  the charts. If you must edit a file that has charts, warn and verify the charts survived.
- **Pivot tables: neither engine can create them.** For pivot output, aggregate with
  `pandas.pivot_table` and write a plain sheet. openpyxl can *read/preserve* existing pivots but
  re-saving may trigger Excel's repair dialog — verify by reopening.
- **Two engines do NOT conflict on import.** (An earlier claim of "stream conflict" was unfounded.)
  The real hazard is opening the *same file path* with two handles simultaneously — don't.

## Formulas — the `<v>0</v>` trap  `[VERIFIED ✓ — 2026-05-31]`

⚠️ **xlsxwriter writes `<v>0</v>` as the cached value for every formula** (unless you pass an explicit
result). Reproduced: `=SUM(A1:A3)` and `=A4*2` both read back as **`0`** via `openpyxl(data_only=True)`
immediately after creation. **openpyxl never computes formulas at all**; `data_only=True` returns the
last *cached* value, and a Python-written file has cache `0` (xlsxwriter) or `None` (openpyxl).

**Consequence for the verify gate**: a soffice render or a `data_only` read of a freshly written file
shows **0 for every formula cell** — this is a *cache* artifact, NOT a real error. Do not let the verify
gate flag these as wrong values.

**To get real computed values, two options:**
1. **Compute in Python, write the value** (not the formula) when the number is what matters.
2. **Recalc via LibreOffice macro** — `soffice --convert-to xlsx` **does NOT recalc** (reproduced:
   stayed `0` after reconvert). You must run the StarBasic macro `ThisComponent.calculateAll()` +
   `store()` (anthropics/skills `recalc.py` pattern: install `Module1.xba`, invoke
   `vnd.sun.star.script:Standard.Module1.RecalculateAndSave`, wrap in `timeout`/`gtimeout`). After
   that, `data_only=True` returns the computed values, and you scan for `#VALUE!`/`#DIV/0!`/`#REF!`/
   `#NAME?`/`#NULL!`/`#NUM!`/`#N/A`.
- **Keep the formula string, never hardcode a stale computed number into a formula cell** (content
  preservation — the spreadsheet's logic is the content).

## Verify gate — different from pptx/docx

Spreadsheets do not proofread by "render every page to image" — print pagination is arbitrary unless
`print_area` is set, so a PDF/JPEG render is unreliable for layout review.
- **Primary gate = structural assertions via openpyxl**: sheet names, expected cells/ranges present,
  formula cells still hold formulas (not overwritten by values), no unexpected `#ERROR`. After a
  recalc, assert the computed values.
- **Render (JPEG) is secondary/optional**, only when a specific visual (a chart, a formatted report
  region) must be eyeballed — and then set `print_area` first. Recipe (if used):
  ```bash
  soffice --headless --convert-to pdf --outdir <dir> <book.xlsx>
  pdftoppm -jpeg -r 150 <book.pdf> <dir>/sheet   # JPEG (see docx/pptx card for the -png first-page bug)
  ```
  Canonical implementation: `references/snippets/render.py::soffice_to_pdf` /
  `references/snippets/render.py::pdf_to_images`.
  (`SAL_USE_VCLPLUGIN=svp` for headless; sandbox socket shim per anthropics/skills `office/soffice.py`.)

## Financial-model authoring conventions (when the deliverable is a model, not just a sheet)

The engine/verify sections above are *mechanism*; this section is the *content standard* for
financial models, budgets, and any analytical workbook a reader will audit. Borrowed from the
anthropics/skills xlsx convention set (2026-06-01) — pure prescriptions, no engine dependency, so
they apply whether `doc-builder` writes via xlsxwriter or openpyxl. Skip for throwaway data dumps;
apply whenever a human will trace the numbers.

**Formulas live in cells, never in Python (load-bearing):**
- **Write Excel formulas (`=SUM(...)`, `=(C4-C2)/C2`, `=AVERAGE(...)`), do NOT compute the number in
  Python and hardcode the result.** A model's logic *is* its content — a hardcoded `=12345` cannot be
  audited, re-run on changed inputs, or trusted. This is the positive rule behind the `<v>0</v>` trap
  above: write the formula string, then recalc via the LibreOffice macro to populate real values.
- **All assumptions in named/separate cells** (growth rates, margins, multiples), and reference those
  cells from formulas — never inline a magic number inside a formula. One input cell, many references.
- **A genuine hardcode (an external input) gets a source comment**: `Source: [system], [date],
  [reference], [URL if any]` (e.g. "Source: SEC EDGAR 10-K, 2025-03, Item 8"). Distinguishes a
  sourced input from an un-auditable guess.

**Color code by cell role** (Excel financial-modeling standard, unless the user specifies otherwise):

| Cell role | Format |
|:---|:---|
| Hardcoded input / scenario parameter | **blue** text (RGB 0,0,255) |
| Formula / calculation | **black** text (RGB 0,0,0) |
| Cross-worksheet link | **green** text (RGB 0,128,0) |
| External-file reference | **red** text (RGB 255,0,0) |
| Key assumption needing attention | **yellow** fill (RGB 255,255,0) |

**Number formats** (so the sheet reads like a model, not a raw dump):
- Years as text (`"2024"`, not `2,024` with a thousands separator).
- Currency `$#,##0`; state units in the header (`Revenue ($mm)`), not per cell.
- Zeros shown as `-` (including in percentage columns).
- Percentages default to `0.0%` (one decimal); multiples as `0.0x` (e.g. EV/EBITDA).
- Negatives in parentheses `(123)`, not a leading minus.

**Pre-build reference sanity check** (cheap, catches whole-model breakage): test 2-3 cell references
before building the full model — confirm column-letter mapping (column 64 = `BL`), Excel's 1-indexed
rows vs. any DataFrame 0-indexing, and cross-sheet ref format (`Sheet1!A1`). Verify gate target after
recalc: **zero formula errors** (`#REF!`/`#DIV/0!`/`#VALUE!`/`#N/A`/`#NAME?`).

## Hard traps

- **Never edit in place.** openpyxl `load → save(same path)` overwrites silently → output ≠ input,
  `shutil.copy2` backup first. (xlsxwriter is write-only so this is moot for it.)
- **openpyxl ≥3.1.4 app.xml change** can make charts mis-render **in Excel** (title overlap / axis
  loss); LibreOffice is unaffected. If Excel compatibility matters, pin `openpyxl ≤3.1.3` or patch app.xml.
- **pandas `mode='a'` (append, openpyxl engine)** can duplicate `app.xml`/`core.xml`/`sheet1.xml` inside
  the zip → file corruption (#39576). Prefer writing all sheets in one pass.
- **openpyxl round-trip drops unsupported conditional-formatting extensions silently** (UserWarning
  on save). If preserving CF on an existing file, capture `warnings.catch_warnings` and verify CF
  count/ranges survived the load→save.
- **Chart types**: xlsxwriter has no Surface/Bubble in older builds; openpyxl has Surface/Bubble but
  see the chart-drop-on-load trap above. Pick the engine by which charts you need AND whether the
  file is new vs existing.

## Version-snapshot policy
Same layout as the pptx/docx cards: the one delivered `outputs/<slug>/current.xlsx`, with version
snapshots and intermediates in the `.omd/<slug>/` work area (`versions/`, `renders/`, `tmp/`). Snapshot
before a large edit. See `references/output-layout.md` for the fixed structure and naming.
