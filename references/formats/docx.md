# Format Knowledge Card — docx

> **What this is**: A data file, not a skill. The OMD agents (`doc-builder`, `doc-verifier`,
> `doc-inspector`) read this card to know the tools, traps, and verified techniques for the
> `.docx` format. Borrow the engine (python-docx / soffice / pdftoppm); the orchestration brain
> lives in the agents and stage skills. Do not duplicate this knowledge into agent files — point
> at this card. Sibling card: `pptx.md` (same discipline, different renderer behavior — esp. math).

## Engine

| Tool | Role | Verified on this machine (2026-05-31) |
|:---|:---|:---|
| `python-docx` 1.2.0 | create / edit paragraphs, styles, tables, sections | ✓ installed |
| `soffice` (LibreOffice) | .docx → .pdf for rendering | resolve on PATH (`command -v soffice` / Windows `where soffice`) |
| `pdftoppm` | .pdf → image (visual proofread) | resolve on PATH |
| `latex2mathml` 3.78.1 + `lxml` | LaTeX → MathML → OMML (editable math, path A) | ✓ installed |
| `matplotlib` 3.9.4 + `Pillow` | LaTeX math → PNG (math path B, fallback) | ✓ installed |

> **Cross-platform tool resolution**: never hardcode an absolute binary path — resolve at run time
> (`command -v soffice`/`command -v pdftoppm`; Windows `where soffice`/`where pdftoppm`). If a tool
> is absent, stop and tell the user how to install it — do not silently skip the render/verify gate.

**Render recipe** (verify/inspect proofreading):
```bash
soffice --headless --convert-to pdf --outdir <dir> <doc.docx>
pdftoppm -jpeg -r 150 <doc.pdf> <dir>/page   # JPEG, ≥150 dpi
```
Canonical implementation: `references/snippets/render.py::soffice_to_pdf` /
`references/snippets/render.py::pdf_to_images`.
> ⚠️ **Use `-jpeg`, not `-png`, when going through PDF for multi-page docs.** `soffice --convert-to png`
> directly (skipping PDF) only emits the **first page** (long-standing LibreOffice bug). Always
> PDF→pdftoppm. (Backported from anthropics/skills office QA recipe, 2026-05-31.)
> **Headless env**: set `SAL_USE_VCLPLUGIN=svp`. In a sandboxed VM where AF_UNIX sockets are blocked,
> soffice needs an `LD_PRELOAD` socket shim (see anthropics/skills `office/soffice.py`); on a normal
> local machine the shim is auto-skipped (`_needs_shim()` returns False).

## Hard traps

- **Never edit in place.** Original is sacred. `doc.save()` to the same path **overwrites with no
  warning** — write to `outputs/<slug>/current.docx`, source file never mutated. Enforce `src != dst`.
- **Provenance lock**: before replacing any text, read and quote the original run first. Never invent
  replacement text (fabricated titles is a logged regression — same rule as pptx).
- **Proofread ALL pages, not just changed ones.** Render every page to image and Read them.
- **`paragraph.text` — getter is safe, SETTER destroys fields.** Reading `v = paragraph.text` is
  read-only (XML untouched). But **assigning** `paragraph.text = "..."` or calling `paragraph.clear()`
  wipes complex content in that paragraph (`w:fldChar` PAGE fields, hyperlinks, bookmarks). To edit
  text in a paragraph that has fields, mutate the specific `run.text`, never the paragraph-level setter.
- **`styles.add_style()` on a duplicate name → ValueError.** Guard with `if name not in doc.styles:`.
- **`add_picture()` default DPI = 72.** Passing width AND height forces a non-proportional resize;
  pass only one to preserve aspect. A 96-dpi screenshot (Windows default) inserted with neither set
  renders ~33% oversized — set an explicit width.
- **`table.merge()` only spans a rectangle** (else `InvalidSpanError`). Call with top-left/bottom-right
  cell pair. After merging, re-iterating the table with `row_cells()` can raise IndexError on some
  merged layouts (python-docx #1434) — handle/avoid re-walking a just-merged table.
- **First-page header is a separate, linked property** (see Headers below): it is NOT reachable
  through the normal `section.header` collection. Mishandling silently drops content.
- **Korean font**: set `Apple SD Gothic Neo` explicitly for KO text (XML `w:rFonts w:eastAsia`), or
  soffice substitutes and the render looks wrong. On a font-less Docker/Linux box, install
  `fonts-noto-cjk` + `fc-cache -fv` first — and re-check **layout** after substitution (a glyph that
  renders is not proof the line-breaks/page-flow survived).
- **Smart quotes in hand-typed insertions**: when you build new run text yourself, curly quotes must
  be XML entities (`&#x201C;` `&#x201D;` `&#x2018;` `&#x2019;`); raw `&`/`<`/`>` must be escaped
  (`&amp;`/`&lt;`/`&gt;`). Validate the part with `ET.fromstring()` before repackaging.

## Headers / footers (3 rules — VERIFIED against python-docx semantics)

1. Setting `section.different_first_page_header_footer = True` does **not** unlink the first-page
   header — `section.first_page_header.is_linked_to_previous` stays **True**. Set it to `False`
   before writing first-page content, or the content lands on the wrong header.
2. Assigning `header.is_linked_to_previous = True` **irreversibly deletes** that header's content.
3. Editing a header that is `is_linked_to_previous` actually edits the **previous section's** header.
- **#1424 trap**: when a regular header AND a first-page header coexist, the XML part mapping can
  drift so first-page-header access returns **silently empty** content. If first_page_header reads
  empty unexpectedly, inspect `word/_rels/document.xml.rels` rId→header part mapping directly.

## Page-number fields (PAGE) — render caveat

A PAGE field is three runs: `begin` fldChar / `instrText` (`xml:space="preserve"`, text `" PAGE "`)
/ `end` fldChar. Injecting this via oxml is structurally correct.
- `[STATUS: VERIFIED ✓ — 2026-05-31]` A 3-page .docx with a `" PAGE "` field in the footer rendered
  the **correct page number** (footer of page 2 showed "2") through soffice→pdftoppm. The feared
  "soffice prints cached value → blank/0" trap did **not** occur for a simple PAGE field — soffice
  computes it at convert time. (The cached-value concern is real for fields soffice can't compute
  headless, e.g. cross-references / TOC page refs — verify those by render before relying.)
- Still: this is the OMML-class discipline — **a field is `VERIFIED` only after a render shows real
  digits**, not because the XML is well-formed. Simple PAGE passed; don't extrapolate to all fields.

## Formulas (inline / block math)

python-docx 1.2.0 has **no math API**. Two paths — path A is **VERIFIED for docx** (unlike pptx).

### Path A — LaTeX → OMML injection  `[STATUS: VERIFIED ✓ with caveats — 2026-05-31]`  ← **default for docx**
Editable native math. Chain: `latex2mathml.convert()` → MathML → `lxml.etree.XSLT(mml2omml.xsl)` →
OMML etree → `paragraph._p.append(omml_root)` (OMML `m:oMath` is a **direct child of `w:p`**, not of
`w:r`). **Proven**: a real .docx with `\hat{x}_k = x_k + K_k(z_k - Hx_k)`, fractions, integrals, sums,
matrices, Greek+subscripts all rendered legibly through soffice → pdftoppm (PNG Read-confirmed).
```python
from latex2mathml.converter import convert
from lxml import etree
omml = etree.XSLT(etree.parse(XSL))(etree.fromstring(convert(latex).encode())).getroot()
paragraph._p.append(omml)
```
**CAVEATS (documented, reproduced 2026-05-31)** — fall back to path B for these:
- **`\hat{x}` accent misaligns** in soffice (hat drifts up-left off the glyph). `\bar` is fine.
- **`\sum` / `\,` (thin space) render as a `□` empty box** — latex2mathml emits an invisible operator
  soffice draws as tofu. (MS Word renders these correctly; the defect is soffice-only — but OMD's
  verify gate is soffice, so treat as a defect.)

### Path B — LaTeX → image embed  `[STATUS: VERIFIED ✓]`  ← **fallback**
matplotlib mathtext → transparent PNG → `add_picture()`. Not editable, but renders identically
everywhere. **Use path B when the formula contains `\hat` or sum/invisible-operator cases above**, or
whenever editable math is not required.
```python
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig = plt.figure(figsize=(4,1)); fig.text(0.01,0.3, rf"${latex}$", fontsize=28)
fig.savefig("eq.png", dpi=300, transparent=True, bbox_inches="tight"); plt.close(fig)
```

### XSL licensing (load-bearing)
- **PoC / local macOS**: `/Applications/Microsoft Word.app/Contents/Resources/mathml2omml.xsl`
  (XSLT 1.0, lxml-direct). **NOT redistributable** (MS EULA) — never ship it in the plugin repo.
- **Distribution**: transpect `mml2omml.xsl` (BSD-2). Note `hub2docx-lib/mml2omml.xsl` is XSLT 2.0 +
  `fix-mml.xsl` include → needs **Saxon-HE** (lxml can't run XSLT 2.0). Bundle Saxon, or find an
  XSLT-1.0 BSD path, before shipping path A in distribution. Linux/CI has no Word XSL at all.

**Rule**: a path is `VERIFIED ✓` only after a real .docx is generated, rendered via soffice→pdftoppm,
and the equation is Read-confirmed legible. Path A passed this (with the two caveats); path B passed clean.

## Editing existing docx — patterns observed in anthropics/skills (technique only, no code copied)

OMD builds with python-docx directly. But for **heavy edits to an existing user docx**, the official
skills' XML-edit discipline is worth borrowing (not the Node `docx-js` generator, and not their
Python `Document`/`DocxXMLEditor` DOM-editor class or `ooxml/scripts/unpack.py`+`pack.py` — see
license note below, and python-docx already covers the same ground, see the three subsections below):
- Tracked changes author = `Claude` (default unless told otherwise). Deleting a whole paragraph must
  also mark the paragraph mark deleted (`<w:del/>` inside `<w:pPr><w:rPr>`) — else an empty paragraph lingers.
- python-docx round-trips untouched unsupported elements (footnotes, etc.) automatically — **as long as
  you don't call the destructive `paragraph.text` setter / `clear()`** (see Hard traps).
- **Adding comments: use python-docx's native `Document.add_comment()`, not raw XML** — no engine
  switch needed at all (see "Comment insertion" below).

> **License note (why no code is copied here)**: anthropics/skills is a **mixed-license repo** — most
> skills are Apache-2.0, but the document skills (`docx`/`pptx`/`xlsx`/`pdf`) are the exception: each
> ships its own `LICENSE.txt` — "© 2025 Anthropic, PBC. All rights reserved... may not... Create
> derivative works... Distribute... to any third party." **Source-available, not open source.** (The
> Apache-2.0 badge on the `awesome-claude-skills` *aggregator* repo's README covers that repo's own
> curation content, not the vendored official Anthropic skill folders it mirrors — this docx folder is
> exactly that proprietary exception, same as `xlsx.md`'s corrected sourcing.) So the three sections
> below describe *workflow/technique only*, reimplemented independently against python-docx + pandoc +
> lxml — no source lines, scripts (`document.py`, `unpack.py`/`pack.py`), or schema files are copied
> from that skill folder into this repo. Pattern observed in anthropics/skills docx (source-available,
> not open source), reimplemented independently, 2026-07-09.

### Redlining workflow (tracked changes on someone else's docx) `[VERIFIED ✓ — 2026-07-09, this machine]`

Scenario this unlocks: **지도교수/공저자 tracked-changes 논문초안 리뷰** — you receive a collaborator's
draft and must return minimal, reviewable tracked changes rather than a silently-rewritten file.

**Engine stays python-docx.** No `docx-js`, no unpack/pack round-trip, no DOM-editor class needed —
python-docx's `oxml` layer (`docx.oxml.OxmlElement`, already how `add_comment` and low-level edits work)
can construct `<w:ins>`/`<w:del>` siblings directly, and `pandoc` (already in this vault's toolchain,
`/opt/homebrew/bin/pandoc` 3.9.0.2 verified) reads them back for verification.

1. **Read the draft with tracked changes preserved** (do NOT silently accept/reject — read what's there):
   ```bash
   pandoc --track-changes=all draft.docx -o draft_with_changes.md
   ```
   Verified output format: `[deleted text]{.deletion author="..." date="..."}[inserted text]{.insertion
   author="..." date="..."}`. `--track-changes=accept`/`reject` silently resolve instead — use `all` for review.
2. **Author the tracked change with python-docx oxml, not `paragraph.text =` (Hard traps rule).**
   Minimal-diff principle (same discipline the official skill states): only wrap the words that actually
   changed in `<w:del>`/`<w:ins>`; leave surrounding text in ordinary untouched runs.
   ```python
   from docx.oxml.ns import qn
   from docx.oxml import OxmlElement

   def make_tracked_replacement(paragraph, old_run_after, del_text, ins_text, author="Claude", rev_id="1"):
       date = "2026-07-09T00:00:00Z"  # use datetime.now(timezone.utc) in real use
       del_el = OxmlElement('w:del')
       del_el.set(qn('w:id'), rev_id); del_el.set(qn('w:author'), author); del_el.set(qn('w:date'), date)
       del_run = OxmlElement('w:r'); del_t = OxmlElement('w:delText'); del_t.text = del_text
       del_run.append(del_t); del_el.append(del_run)
       old_run_after._r.addnext(del_el)

       ins_el = OxmlElement('w:ins')
       ins_el.set(qn('w:id'), str(int(rev_id)+1)); ins_el.set(qn('w:author'), author); ins_el.set(qn('w:date'), date)
       ins_run = OxmlElement('w:r'); ins_t = OxmlElement('w:t'); ins_t.text = ins_text
       ins_run.append(ins_t); ins_el.append(ins_run)
       del_el.addnext(ins_el)
   ```
   **Reproduced this session**: `"The term is 30 days."` → run split into `"The term is "` (untouched) +
   `<w:del>30</w:del>` + `<w:ins>60</w:ins>` + `" days."` (untouched).
3. **Verify by render, not just XML validity** — same discipline as the PAGE-field rule above.
   `soffice --convert-to pdf` → `pdftoppm` → Read the JPEG. `[STATUS: VERIFIED ✓]` this session: the
   rendered page showed strikethrough **30**, underlined **60**, and a change bar in the margin — the
   real Word tracked-changes visual, not just correct-looking XML.
4. **Verify the resulting text with pandoc**, both to confirm the edit landed and that reject/accept
   resolve correctly:
   ```bash
   pandoc --track-changes=all reviewed.docx -o verify.md   # both spans visible, correct author/date
   pandoc --track-changes=accept reviewed.docx -o final.md # "The term is 60 days." (new text wins)
   grep "30 days" final.md   # should NOT match
   ```
5. **Batch related edits, don't do the whole document as one script.** Group 3-10 changes per batch
   (by section/type/proximity — same guidance as the official skill), re-grep the current
   `word/document.xml` (or re-locate the paragraph via python-docx) before each batch since prior edits
   shift things.

Everything above ran and produced the exact evidence stated — this section is `VERIFIED`, not
`[unverified — backport]`, for the case exercised (authoring a fresh tracked change on a plain-text
run). **`[unverified — backport]`**: rejecting/accepting an *existing other-author* tracked change
(nested `<w:ins>`/`<w:del>` from a prior reviewer) — same oxml-sibling-insert technique should apply to
the existing element rather than a plain run, but this was not exercised this session. Promote to
`VERIFIED` after a real multi-author draft round-trip.

### OOXML XSD schema validation `[VERIFIED ✓ — 2026-07-09, this machine]`

Confirms a generated/edited docx's `word/document.xml` is structurally valid **before** shipping it —
catches schema violations (bad element ordering in `<w:pPr>`, malformed tracked-change nesting) that
soffice may silently tolerate or mis-render instead of rejecting.

**Engine: `lxml.etree.XMLSchema`** (already in the engine table for math/OMML — no new dependency).
The schema itself is the public **ECMA-376 / ISO/IEC 29500 WordprocessingML** standard (`wml.xsd`),
obtainable directly from ecma-international.org/ISO — **not vendored into this repo** (avoids the
anthropics/skills proprietary-license question entirely; we reference the public standard, not their
copy of it).

```python
from lxml import etree
schema = etree.XMLSchema(etree.parse("wml.xsd"))  # ECMA-376/ISO-29500 Part 4, obtained separately
valid = schema.validate(etree.parse("unpacked/word/document.xml"))
if not valid:
    for e in schema.error_log:
        print(e)  # line, column, message
```
**Reproduced this session**: `wml.xsd` compiled in <0.1s (no unresolved includes/imports), and a real
`word/document.xml` (containing the tracked-change runs from the redlining test above) validated `True`
with zero errors. Use as a pre-flight gate in `doc-builder`/`doc-verifier` alongside the existing
render-based checks — schema validity is necessary but not sufficient (a schema-valid file can still
mis-render; keep the soffice→pdftoppm→Read gate as the visual authority).

### Comment insertion `[VERIFIED ✓ — 2026-07-09, this machine]`

python-docx 1.2.0 has a **native comment API** — `Document.add_comment()` — so this needs **no XML
injection at all**, unlike the anthropics/skills approach (their `comment.py` boilerplate against the
DOM-editor class). This is a straight engine-native win.

```python
from docx import Document
doc = Document("draft.docx")
paragraph = doc.paragraphs[0]
doc.add_comment(runs=paragraph.runs[0], text="Please verify this claim.", author="Claude", initials="C")
doc.save("outputs/<slug>/current.docx")
```
- `runs` accepts a single `Run` or a sequence (e.g. `paragraph.runs` for a whole paragraph) — python-docx
  anchors the comment range from the first run to the last, using `w:commentRangeStart`/`w:commentRangeEnd`.
- Comment placement is on **even run boundaries only** — you cannot anchor mid-run; split the run first
  (or run-level edit per Hard traps) if the comment must start/end inside a run.
- **Reproduced this session**: `doc.add_comment(...)` → `doc.save()` → reopened with `Document(path)` →
  `doc.comments[0].author/.text` read back correctly (`"Claude"` / `"Please verify this claim."`) → the
  file also converted cleanly via `soffice --convert-to pdf` (no corruption). Pandoc also surfaces the
  comment as a `{.comment-start/.comment-end}` span when converting to markdown, useful for text-only review.
- Use for: reviewer-style annotations without altering document text (complements the redlining workflow
  above — comments explain *why*, tracked changes show *what* changed).

## Version-snapshot policy
Same layout as the pptx card: the one delivered `outputs/<slug>/current.docx`, with version snapshots
and renders in the `.omd/<slug>/` work area (`versions/`, `renders/`, `tmp/`). Snapshot only before a
large edit. See `references/output-layout.md` for the fixed structure and naming.
