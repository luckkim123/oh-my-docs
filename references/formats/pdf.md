# Format Knowledge Card — pdf (input-side)

> **What this is**: A data file, not a skill. The OMD agents (`doc-builder`, `doc-verifier`,
> `doc-inspector`) read this card to know the tools, traps, and verified techniques for **PDF as
> an input format** — parsing, table extraction, form filling, OCR. Borrow the engine (pdfplumber /
> pypdf / reportlab); the orchestration brain lives in the agents and stage skills. Sibling cards:
> `pptx.md`, `docx.md`, `xlsx.md`, `hwpx.md` (same discipline). **Scope split from `docs-convert`**:
> this card is PDF **input** (reading an existing PDF someone hands you); `docs-convert` /
> `references/conversions.md` owns PDF **output** (another format → PDF as a deliverable). A request
> to "extract this PDF's table" or "fill this PDF form" is this card; "export my slides to PDF" is
> `docs-convert`.

> **License note (load-bearing)**: pattern observed in anthropics/skills `document-skills/pdf`
> (source-available, not open source), reimplemented independently with `pypdf`/`pdfplumber`/
> `reportlab`, 2026-07-09. ⚠️ The upstream `LICENSE.txt` in that skill folder is a **proprietary**
> Anthropic Services-usage license (no redistribution, no derivative works, no reproduction/copying,
> no extraction outside the Services) — it is **not** Apache-2.0, and no upstream `.py` source or
> OOXML/PDF-structure code from that folder is copied or derived into this card or anywhere in this
> repo. This card records only *technique knowledge* (which library does what, which traps are
> real) restated and independently re-verified in our own words and our own code, the same
> discipline already applied to the xlsx/pptx/docx cards for their upstream sources. The individual
> libraries this card recommends (`pypdf`, `pdfplumber`, `reportlab`, `pypdfium2`) are themselves
> separately and permissively licensed — see Engine table — and none of their code is copied either,
> only their public APIs are called.

## Engine — three libraries, explicit routing

| Tool | Role | License | Verified on this machine (2026-07-09) |
|:---|:---|:---|:---|
| `pypdf` 6.14.2 | merge / split / rotate / metadata / encrypt / **AcroForm fill** | BSD | ✓ installed + exercised (venv) |
| `pdfplumber` 0.11.10 | text extraction with layout, **table extraction** | MIT | ✓ installed + exercised (venv) |
| `reportlab` 5.0.0 | create new PDFs from scratch (canvas / Platypus) | BSD | ✓ installed + exercised (venv, used only to generate test fixtures) |
| `pypdfium2` | render page → PNG (fast, PDFium/Chromium binding) | Apache/BSD | unverified on this machine (not installed) |
| `pytesseract` + `pdf2image` | OCR scanned/image-only PDFs | Apache-2.0 / MIT | unverified on this machine (not installed; `tesseract` CLI itself **is** present via `command -v tesseract`) |
| `pdftotext` / `pdftoppm` / `pdfimages` (poppler-utils) | CLI text/image extraction | GPL-2 | ✓ present on PATH (`command -v`) — not functionally exercised this pass |
| `qpdf`, `pdftk` | CLI merge/split/repair/encrypt | Apache / GPL | **not installed** on this machine (`command -v` → not found) — do not claim available without checking first |

**Routing rule (load-bearing):**
- **Read text / extract tables** → `pdfplumber`. Best table-structure fidelity of the options tried.
- **Merge / split / rotate / metadata / encrypt / AcroForm form-fill** → `pypdf`. Pure Python, no
  subprocess, cross-platform.
- **Create a brand-new PDF from scratch** (e.g. render a filled form as flattened output, or build a
  report) → `reportlab` (Canvas for free-form layout, Platypus/`SimpleDocTemplate` for flowing
  text+tables).
- **Render page → image** (for visual bbox verification, or OCR preprocessing) → prefer
  `pdftoppm` (already on PATH, no extra install) over `pypdfium2` unless a Python-native handle is
  specifically needed. `pypdfium2` is unverified here — resolve/install before relying on it.
- **Scanned/image-only PDF** (no text layer at all) → OCR path (`pytesseract` + `pdf2image`, or
  `tesseract` CLI directly on a `pdftoppm`-rendered PNG). Unverified end-to-end on this machine;
  `tesseract` binary confirmed present, the Python bindings were not installed/tested this pass.
- **This machine's Python note**: `/usr/bin/python3` is Xcode's bundled 3.9.6 (mismatched — see
  `machine_python_xcode_39_mismatch` memory). All verification below used `brew`'s `python3.12` in a
  throwaway venv (`python3.12 -m venv`), not the system interpreter, and not a `pip install
  --break-system-packages` into brew's managed environment. **Do the same** — install into a venv,
  never `--break-system-packages` into the Homebrew-managed interpreter (PEP 668 externally-managed
  guard exists for a reason).

## Text extraction — real behavior, not upstream's claim  `[VERIFIED ✓ / ⚠️ mixed — 2026-07-09]`

Reproduced on this machine with a throwaway venv (`python3.12 -m venv`, `pip install pdfplumber
pypdf reportlab`):

- **`pypdf` `page.extract_text()`** — plain English text extracts correctly (word content intact).
  `[VERIFIED ✓ — 2026-07-09]`
- **`pdfplumber` `page.extract_text()` / `extract_tables()`** — correctly extracts English text and
  reconstructs table row/column structure from a `reportlab`-generated table.
  `[VERIFIED ✓ — 2026-07-09]`
- ⚠️ **Korean (or any non-Latin) text in a `reportlab`-built PDF extracts as garbage** (`n`
  replacing every Korean glyph) — reproduced directly: `extract_text()` on a Korean-labeled table
  returned `'nnn nn nn'` where the source string was `'출장비 정산 내역'`. **Root cause isolated: this
  is a `reportlab` *authoring* defect (Helvetica has no Korean glyphs; reportlab silently substitutes
  a fallback/notdef glyph), not a pdfplumber/pypdf *reading* defect** — the PDF's actual embedded
  glyph stream is malformed at creation time, so no reader can recover the Korean text. **Practical
  consequence for this vault's use case** (연구비 정산 양식, 출장 서류): if you ever need to *generate*
  a Korean PDF with `reportlab`, you must register a CJK-capable font first (e.g.
  `reportlab.pdfbase.cidfonts.UnicodeCIDFont` with an HeiseiMin/STSong-family font, or embed a local
  Korean TTF via `pdfmetrics.registerFont`) — plain `Helvetica`/`Times-Roman` will silently corrupt
  Korean text with no error raised. This card's scope is PDF *input*, so this is a boundary note:
  **when extracting text from a real-world Korean PDF that some other tool produced properly (Hancom,
  MS Word-to-PDF, etc.), this defect does not apply** — it is specific to naively using reportlab
  without CID font registration.
- ⚠️ **Ligature mis-decode on a real-world embedded-font PDF** — tested against a genuine
  vendor datasheet already in this vault (`Sonoptix_ECHO_Datasheet.pdf`, not a reportlab fixture):
  `pdfplumber.extract_text()` returned `Sonop�x` for "Sonoptix" and `naviga�tion` for
  "navigation" — the `ti`/`fi`-style ligature glyph decoded to U+FFFD (replacement character)
  instead of the correct letter pair. **This is a real risk for any real-world PDF, independent of
  language**: some embedded fonts map ligature glyphs outside pdfplumber's (or the font's `ToUnicode`
  CMap's) expected range. **Practical mitigation**: after extraction, scan the output for `�`
  (U+FFFD) and treat any hit as "extraction is lossy here" — do not silently trust the string. For
  research-appendix table extraction (a named use case), spot-check extracted numbers/labels against
  the source PDF rendered to image, don't take `extract_text()` output as ground truth unseen.

## Table extraction — verified structure, tune before trusting numbers

- **Default `extract_tables()` (no settings) correctly reconstructed a 4-row × 3-column table**
  (header + 3 data rows) from a `reportlab`-built grid table, cell-for-cell, on the first try.
  `[VERIFIED ✓ — 2026-07-09]`
- Upstream's advanced `table_settings` (`vertical_strategy="lines"`, `snap_tolerance`,
  `intersection_tolerance`) is **plausible but unverified on this machine** — only the
  no-argument default path was exercised. For a table with no visible ruling lines (whitespace-
  aligned instead of gridded), the default `vertical_strategy="lines"` will likely find zero tables;
  switching to `"text"` strategy is the documented pdfplumber escape hatch, but treat it as
  **unverified (upstream claim)** until tried against an actual borderless table.
- **Visual debug recipe** (upstream's own suggestion, structurally sound, not independently
  re-verified this pass): `page.to_image(resolution=150).save("debug_layout.png")` — render the page
  with pdfplumber's own overlay to see what it thinks the table boundaries are, before trusting
  `extract_tables()` blindly on a complex layout.
- **For 논문 부록 표 추출 (paper-appendix table extraction)**: prefer combining pdfplumber's per-page
  `extract_tables()` with a `pandas.DataFrame(table[1:], columns=table[0])` per table, then
  `pd.concat` — this is upstream's pattern and structurally matches the xlsx card's "hand off a
  dataframe, not a formula" boundary. Unverified end-to-end (dataframe conversion not exercised this
  pass, only the raw list-of-lists table extraction was).

## Form filling — AcroForm (fillable) vs. non-fillable (bbox annotation)

Two structurally distinct paths, distinguished by whether the PDF actually has an `/AcroForm`
dictionary — **detect first, never assume.**

### Detection  `[VERIFIED ✓ — 2026-07-09]`
```python
from pypdf import PdfReader
reader = PdfReader("form.pdf")
fields = reader.get_fields()   # None if no fillable fields, dict of Field objects if present
has_acroform = "/AcroForm" in reader.trailer["/Root"]
```
Reproduced: a plain non-form PDF returns `get_fields() == None` and `"/AcroForm" not in
trailer["/Root"]` — both signals agree, matching the upstream `check_fillable_fields.py` script's
branch logic (`if reader.get_fields(): ... else: ...`). This routing logic is sound; carry it
forward as-is. **Not tested against an actual AcroForm-bearing PDF this pass** (no fillable PDF was
available in the test environment) — the *presence* check is verified, the *fill* step below is
upstream's documented approach, unverified end-to-end here.

### Tier 1 — AcroForm fillable fields (preferred when present)
1. Detect via `get_fields()` (above).
2. Enumerate each field's `field_id`, `page`, `rect` (bbox in PDF coords, y=0 at page bottom),
   and `type` (`text` / `checkbox` / `radio_group` / `choice`). Checkboxes carry `checked_value`/
   `unchecked_value`; radio groups carry a `radio_options` list with per-option `value`+`rect`;
   choice fields carry `choice_options` with `value`+display `text`.
3. **Cross-reference against a rendered PNG of the page** before assigning values — a field ID like
   `Text_12` tells you nothing about *purpose* without seeing where it sits on the page. Render via
   `pdftoppm -png -r 150` (already verified present on this machine) and inspect visually.
4. Fill via `pypdf.PdfWriter.update_page_form_field_values(page, {field_id: value}, auto_regenerate=False)`,
   then `writer.set_need_appearances_writer(True)` — **this second call matters**: many PDF viewers
   won't visually render the filled value until the appearance-regeneration flag is set, even though
   the underlying field value is correctly written. This is a documented behavior from the upstream
   script's own inline comment, structurally consistent with how AcroForm appearance streams work —
   not independently re-verified against a real form this pass, carry forward as **unverified
   (documented upstream, plausible)**.
5. ⚠️ **Known pypdf bug (documented directly in upstream's script source, not a marketing claim)**:
   pypdf ≥5.7.0 raises `TypeError` when writing a **choice/selection-list** field's value, because
   `DictionaryObject.get_inherited(FA.Opt)` returns a list of `[value, display_text]` pairs and
   pypdf's writer tries to `"\n".join()` them directly (expects flat strings). The upstream fix is a
   runtime monkeypatch of `get_inherited` that flattens the pair-list to just the value strings
   before writing. **Only affects choice/dropdown fields** — text/checkbox/radio are unaffected. If
   a target form has a dropdown field, either apply this monkeypatch or hand-verify the field can
   still be written; do not assume pypdf's default path silently works for choice fields.
6. **Validate before writing**: check every `field_id` you're about to set actually exists in the
   form and the `page` matches — writing to a nonexistent field ID fails silently in some pypdf
   versions rather than erroring. Build a `field_id → field_info` map first, reject unknowns loudly.

### Tier 2 — Non-fillable (flat/scanned form, no AcroForm)
No native form fields exist — you must locate label/entry regions **visually** and add text as
**annotations** (not editable form fields, just positioned text draws). Sound approach, upstream's
own structured method, unverified end-to-end on this machine (no real non-fillable form tested this
pass) but the reasoning is self-consistent and worth carrying forward as the default procedure:
1. Render the PDF to PNG (one image per page, `pdftoppm -png -r 150` — already verified present).
2. Visually identify each field: a **label** bounding box (the printed prompt, e.g. "성명:") and a
   separate, **non-overlapping entry** bounding box (where the answer goes — beside/below/above the
   label depending on layout, or the small square itself for a checkbox — never the checkbox's
   label text). Common Korean-form layouts (label-then-blank-cell, label-then-underline,
   label-above-signature-line) all reduce to this same label-vs-entry bbox split.
3. Record bboxes in image-pixel coordinates (top-left origin), distinct from AcroForm's PDF-coordinate
   `rect` (bottom-left origin, y=0 at page bottom) — **do not mix the two coordinate systems.**
4. **Validate before writing, twice**: (a) mechanically check no label/entry bbox pairs intersect and
   entry boxes are tall enough for the font size; (b) **visually re-render** the boxes as colored
   overlays (e.g. red = entry, blue = label) on top of the page image and actually look at it — a
   box that "looks right" in JSON coordinates can still be misplaced on the real page. Skipping the
   visual check is the most likely failure mode (bbox off by a row, or covering the label instead of
   the blank).
5. Add the annotation text at the entry bbox (font size/color as needed) and re-save as a new file —
   never overwrite the source PDF (see Hard traps).
6. **For checkboxes specifically**: target ONLY the small square glyph (□/☐) as the entry bbox, not
   the adjacent "Yes"/"No" text — the label bbox covers the text, the entry bbox covers just the box.

## OCR — unverified, flag honestly

Neither `pytesseract` nor `pdf2image` are installed on this machine; only the `tesseract` CLI binary
itself is present (`command -v tesseract` succeeds). **Do not claim OCR works until actually run**:
the documented path (`pdf2image.convert_from_path` → PIL images → `pytesseract.image_to_string`)
is structurally standard and widely used, but is `[UNVERIFIED on this machine — 2026-07-09]`. If a
receipt/영수증 PDF turns out to have no text layer (`pdfplumber`/`pypdf` extract empty string), the
concrete next step is: render each page via `pdftoppm` (already verified present, no extra install),
then run `tesseract <page>.png stdout -l kor+eng` directly via the CLI (avoids installing
`pytesseract`/`pdf2image` at all) — `-l kor+eng` for mixed Korean/English receipts, unverified this
pass but a standard tesseract invocation.

## Hard traps

- **Never edit in place.** Read the source PDF, write to a new path — same discipline as every
  sibling card. A filled/annotated/merged PDF is a **new file**, the input is never mutated.
- **`get_fields()` returning `None` is a valid, common result** — it means "not a fillable form,"
  not an error. Branch on it explicitly (Tier 1 vs Tier 2 above); don't treat `None` as failure.
- **PDF coordinate origin is bottom-left (y=0 at page bottom)**; PNG/image coordinates are top-left
  (y=0 at page top). AcroForm `rect` values and hand-drawn annotation bboxes on a rendered image use
  *different* y-axis directions — convert explicitly, never assume they match.
- **`reportlab`-authored PDFs with non-Latin text are a trap for output, not input** — see Text
  extraction section above. This matters for this card only as a "don't accidentally create a
  Korean-broken PDF while testing/fixture-building"; real-world input PDFs from Hancom/Word/Acrobat
  do not typically have this defect (their font embedding handles CJK correctly).
- **U+FFFD (`�`) in extracted text = a silent lossy-extraction signal.** Always scan extracted
  text for this character; its presence means specific glyphs (often ligatures) failed to map — do
  not present that text as a faithful transcript without flagging the gap.
- **`qpdf` and `pdftk` are NOT installed on this machine** (verified: `command -v` finds neither).
  Upstream's reference.md leans on `qpdf` for several CLI recipes (linearize, complex page-range
  merge, repair) — those recipes are **unavailable as-is** until `brew install qpdf` (or equivalent)
  is run. Don't propose a `qpdf` command as if it just works; check `command -v qpdf` first, same
  cross-platform-resolution discipline as the sibling cards.
- **This machine's default `python3` is Xcode's mismatched 3.9.6** (see
  `machine_python_xcode_39_mismatch` memory) — always target `python3.12` (or a venv built from it)
  for any of the libraries in the Engine table above, and always via a venv, never
  `--break-system-packages` into the Homebrew-managed interpreter.

## Version-snapshot policy

PDF input-processing (extraction, form-fill) is typically a **one-shot transform**, not an iterative
editing session like pptx/docx — so the version-snapshot machinery (`versions/`, `v{NN}_...`) mostly
does not apply. What does carry over from `references/output-layout.md`: the **filled/merged/split
output is the one delivered `outputs/<slug>/current.pdf`** (or `.xlsx`/`.md` when the output of a
table-extraction job is a spreadsheet or markdown table, not a PDF), never overwriting the source;
intermediate renders (`pdftoppm` PNGs used for bbox validation) live in `.omd/<slug>/renders/` /
`.omd/<slug>/tmp/`, same as every other format card, and are pruned at terminal cleanup.
