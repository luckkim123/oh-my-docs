---
name: docs-pdf
description: |
  PDF input-side processing — parse an existing PDF: extract text/tables, fill a form (AcroForm
  or non-fillable bbox annotation), or OCR a scanned/image-only PDF. This is reading/filling an
  existing PDF someone hands you, NOT exporting a document to PDF (that is docs-convert's job —
  see Do_Not_Use_When).
  Triggers: PDF 폼 채우기, PDF 양식 채워줘, PDF 표 추출, PDF에서 표 뽑아줘, 영수증 PDF 읽어줘,
  PDF 텍스트 추출, PDF 파싱, PDF 병합, PDF 나누기, PDF 합쳐줘, 정산 양식 PDF, 출장 서류 PDF,
  fill pdf form, extract pdf table, parse pdf, read pdf form, merge pdf, split pdf, ocr pdf,
  scanned pdf text
---

# docs-pdf — PDF Input Processing

<Purpose>
Process an existing PDF handed to you: extract text/tables, fill in a form (AcroForm fillable
fields, or visually-placed annotations when no fillable fields exist), merge/split/rotate pages,
or OCR a scanned/image-only PDF. Read `references/formats/pdf.md` for the engine routing, verified
findings, and hard traps — this skill is a thin dispatch layer, the knowledge lives in the card.
</Purpose>

<Use_When>
- "이 PDF 표 좀 뽑아줘" / "extract the table from this PDF" — 논문 부록 표, 실험 데이터 표 등
- "이 정산 양식 PDF 채워줘" / "fill this expense form" — 연구비 정산, 출장 서류 같은 PDF 양식
- "이 영수증 PDF에서 텍스트 읽어줘" / scanned receipt with no text layer → OCR path
- Merge/split/rotate an existing multi-page PDF
- Any task where the **input** is a PDF and you need to get structured content OUT of it
</Use_When>

<Do_Not_Use_When>
- **Producing** a PDF as a deliverable from another format (.pptx/.docx → .pdf) → `docs-convert`
  owns PDF as an **output** format. This is the load-bearing role split — see the card's opening
  note. "발표자료를 PDF로 변환/내보내기" is `docs-convert`, never this skill.
- Building a brand-new document from scratch that happens to render to PDF as its final step in
  the OMD pipeline → `docs-build` (pptx/docx/hwpx/xlsx), then `docs-convert` if a PDF deliverable
  is also needed.
- The PDF is just a reference/source material to *read for content* during document planning (not
  to extract structured data from) → the analyzer stage in `docs-intake`/`docs-plan` reads PDFs
  directly as source material; this skill is for extraction/fill/merge as the primary task itself.
</Do_Not_Use_When>

<Format_Knowledge>
`references/formats/pdf.md` is the single source of truth: engine routing (pdfplumber / pypdf /
reportlab / OCR), what is actually `[VERIFIED ✓]` on this machine vs. flagged unverified, the
Korean-text-in-reportlab trap, the ligature mis-decode (U+FFFD) trap, AcroForm vs. non-fillable
form-fill procedures, and the PEP-668 venv note for this machine's Python setup. Do not duplicate
that knowledge here — read the card before acting.
</Format_Knowledge>

<Gate>
**Extraction tasks** (text/table): after extracting, scan the output for U+FFFD (`�`) — its
presence means some glyphs (often ligatures) failed to decode; report this explicitly rather than
presenting the text as a faithful transcript. For tables, spot-check extracted values against the
source PDF (rendered to image) before treating numbers as ground truth.

**Form-fill tasks**: detect AcroForm presence first (`reader.get_fields()`), never assume a form
type. Before writing any field, confirm the field ID actually exists in the form (build an ID→info
map, reject unknowns loudly) and cross-reference bounding boxes against a rendered PNG. For
non-fillable forms, the visual bbox validation (mechanical intersection check + actual eyeball of a
rendered overlay image) is REQUIRED, not optional — do not skip straight from bbox guess to output.

**Never edit in place** — the source PDF is never mutated; output is always a new file.
</Gate>

<Steps>
1. Read `references/formats/pdf.md` for the routing table and traps relevant to the task at hand.
2. **Text/table extraction**: use `pdfplumber` (`extract_text()` / `extract_tables()`). Scan for
   U+FFFD, spot-check tables. If the PDF has no text layer at all (empty extraction on a page that
   visibly has content), fall through to the OCR path.
3. **Form fill**: detect fillable fields via `pypdf.PdfReader.get_fields()`.
   - **Fillable (AcroForm present)**: enumerate field types (text/checkbox/radio_group/choice),
     render the page to confirm field purpose visually, fill via
     `writer.update_page_form_field_values(...)` + `writer.set_need_appearances_writer(True)`.
     Watch for the documented pypdf choice-field bug (card's Tier 1, point 5) if the form has a
     dropdown.
   - **Non-fillable**: render to PNG, visually determine label/entry bounding boxes (never
     overlapping), validate mechanically AND visually (rendered overlay), then add positioned text
     annotations at the entry boxes.
4. **Merge/split/rotate/metadata**: `pypdf.PdfWriter`/`PdfReader` — straightforward, verified on
   this machine (see card).
5. **OCR (scanned/image-only PDF)**: render pages via `pdftoppm` (verified present on this
   machine), then either `tesseract <page>.png stdout -l kor+eng` directly via CLI, or
   `pytesseract`/`pdf2image` if installed. This path is unverified end-to-end on this machine —
   say so, and confirm the actual output looks right before presenting it as done.
6. Write output to `outputs/<slug>/` per `references/output-layout.md` (never overwrite the input
   PDF). For extraction tasks producing a table, the output is typically `.xlsx`/`.md`, not a PDF —
   name it by what it actually is.
</Steps>

<Output>
Depending on task: extracted text/markdown, an `.xlsx` of extracted tables, a filled `.pdf` (new
file, source untouched), or split/merged/rotated `.pdf` output(s) — all under `outputs/<slug>/`.
Report explicitly what was verified vs. what carries an unverified/lossy-extraction flag (U+FFFD
hits, OCR not exercised on this machine, etc.) — do not round up to "done" past what was actually
checked.
</Output>

<License_Note>
`references/formats/pdf.md`'s technique knowledge is a pattern observed in anthropics/skills
`document-skills/pdf` (source-available, not open source — proprietary Anthropic Services-usage
license, no redistribution/derivative-works), reimplemented independently with
`pypdf`/`pdfplumber`/`reportlab`, 2026-07-09. No upstream source code is copied or vendored into
this skill or the card; only the underlying, separately-and-permissively-licensed Python libraries'
public APIs are used.
</License_Note>
