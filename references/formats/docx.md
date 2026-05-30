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

## Editing existing docx — borrowed discipline (anthropics/skills, pattern only)

OMD builds with python-docx directly. But for **heavy edits to an existing user docx**, the official
skills' XML-edit discipline is worth borrowing (not the Node `docx-js` generator):
- Tracked changes author = `Claude` (default unless told otherwise). Deleting a whole paragraph must
  also mark the paragraph mark deleted (`<w:del/>` inside `<w:pPr><w:rPr>`) — else an empty paragraph lingers.
- python-docx round-trips untouched unsupported elements (footnotes, etc.) automatically — **as long as
  you don't call the destructive `paragraph.text` setter / `clear()`** (see Hard traps).
- The official `comment.py` is an allowed exception to "edit existing via XML" — boilerplate Python is
  fine for adding comments (pre-escape text: `&amp;`, `&#x2019;` for smart quotes).

## Version-snapshot policy
Same layout as the pptx card: the one delivered `outputs/<slug>/current.docx`, with version snapshots
and renders in the `.omd/<slug>/` work area (`versions/`, `renders/`, `tmp/`). Snapshot only before a
large edit. See `references/output-layout.md` for the fixed structure and naming.
