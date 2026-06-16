# Format Knowledge Card — pptx

> **What this is**: A data file, not a skill. The OMD agents (`doc-builder`, `doc-verifier`,
> `doc-inspector`) read this card to know the tools, traps, and verified techniques for the
> `.pptx` format. Borrow the engine (python-pptx / soffice / pdftoppm); the orchestration brain
> lives in the agents and stage skills. Do not duplicate this knowledge into agent files — point
> at this card.

## Engine

| Tool | Role | Verified on this machine (2026-05-28) |
|:---|:---|:---|
| `python-pptx` 1.0.2 | create / edit shapes, text, layout | ✓ installed |
| `soffice` (LibreOffice) | .pptx → .pdf for rendering | resolve on PATH (`command -v soffice` / Windows `where soffice`) |
| `pdftoppm` | .pdf → .png (visual proofread) | resolve on PATH (`command -v pdftoppm` / Windows `where pdftoppm`) |
| `matplotlib` 3.9.4 + `Pillow` 11.3 | LaTeX math → PNG (formula path B) | ✓ installed |

> **Cross-platform tool resolution**: never hardcode an absolute binary path — resolve at run time.
> macOS/Linux: `command -v soffice` / `command -v pdftoppm`.
> Windows: `where soffice` (default `C:\Program Files\LibreOffice\program\soffice.exe`);
> `pdftoppm` ships with poppler (`where pdftoppm`, or via `winget install`/`choco install poppler`).
> If a tool is absent, stop and tell the user how to install it — do not silently skip the render/verify gate. (Windows paths documented, unverified on this machine.)

**Render-to-PNG recipe** (used by verify/inspect for proofreading):
```bash
soffice --headless --convert-to pdf --outdir <dir> <deck.pptx>
pdftoppm -png -r 150 <deck.pdf> <dir>/slide   # ≥150 dpi — low dpi hides overlap
```

## Building on a master template — clone layouts, do NOT hand-draw

> When the user supplies a designed master template (`.pptx` with real layouts), the deck must be
> built by **instantiating those layouts**, never by adding blank slides and drawing TextBoxes by
> hand. Hand-drawn boxes lose the template's Contents page, flag icons, centered-title placement,
> and number formatting — the exact `2026-06-16` herolab regression (v1–v3). `docs-standardize`
> must run first to extract the layout/placeholder map; this card assumes that map exists.

- **Add slides from a layout, fill placeholders — never `add_textbox` on a blank slide.**
  `slide = prs.slides.add_slide(prs.slide_layouts[idx])` then write into the inherited placeholders
  (`slide.placeholders[ph_idx]`). The layout carries font, color, bullet/number style, and position;
  a hand-drawn `add_textbox` inherits none of it and silently diverges from the template.
- **Find the right layout/placeholder indices first, don't guess.** Indices are template-specific.
  Dump them once: `for i,l in enumerate(prs.slide_layouts): print(i, l.name)` and
  `for p in slide.placeholders: print(p.placeholder_format.idx, p.placeholder_format.type, p.name)`.
  (herolab map, for reference: layouts `[1]=Title [2]=Contents [3]=Content`; Content body placeholder
  `idx 1`, slide-number `idx 12`. Re-dump for any other template — do not hardcode these.)
- **Empty placeholders left unfilled still render** as the template's prompt text ("Click to add…").
  Either fill every placeholder you instantiated or remove the shape; verify catches leftover prompts.

## python-pptx high-level API traps (the v4/v5 class — code correctness, not XML)

> The XML/zip traps below are about repackaging. **These are about the everyday python-pptx calls
> the builder makes on every run** — the layer that broke v4/v5 on `2026-06-16`. Sibling `docx.md`
> documents the equivalent `paragraph.text` setter trap; pptx had the same hazard undocumented.

- **`text_frame.text = "..."` (and `paragraph.text = ...`) DESTROYS inherited run formatting**
  `[VERIFIED ✓ — 2026-06-16, python-pptx 1.0.2]`. Probed: after `body.text_frame.text = "..."`,
  the new run's `font.size`, `font.name`, and `font.color.type` are **all `None`** — the setter
  replaces the paragraph's runs with one bare run carrying **no `rPr`**, so the placeholder's
  inherited font (e.g. Arial), color, and number/bullet style collapse to the theme default
  (Calibri) and the numbering vanishes. To set text while keeping inherited style, write the **run**
  level: keep/clear runs deliberately and set `run.text`, or set the text then re-assert
  `run.font.name/size/color` explicitly. Never use the frame/paragraph-level `.text` setter on an
  inherited placeholder.
- **A run with no explicit `size` falls back to the master `bodyStyle` (often 28pt)**
  `[VERIFIED ✓ — 2026-06-16: a fresh run's font.size is None]`. If you build runs yourself, set
  `run.font.size` explicitly (`Pt(16)` etc.) — an unset size does NOT inherit the layout's intended
  size, it falls through to the slideMaster's `bodyStyle`, overflowing tight boxes.
- **A shape's box dims are independently mutable, and a 0-width box hides its text**
  `[VERIFIED ✓ — 2026-06-16: `shape.width = 0` is accepted and leaves width at 0]`. If you set only
  `top` (or any subset) on a shape whose other dims were never assigned, the unset ones stay 0 → a
  `width=0` box whose text is **invisible** on the render while still present on disk (the
  silent-failure cousin of the namespace ghost). When you position/resize a shape, assign all four
  of `left/top/width/height` together.
- **A fixed-height box without autofit overflows; a long title without wrap-control invades the
  header** `[from 2026-06-16 — v5]`. For body text that may run 6–7 lines, either enable autofit
  (`text_frame.word_wrap = True` + `auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE`) or give the box
  enough height. For titles, keep them one line (the template's title box assumes single-line height).
- **Paragraph level indexing: python-pptx `paragraph.level` is 0-based, but the master's `lstStyle`
  defines them as `a:lvl1pPr` (=level 0), `a:lvl2pPr` (=level 1), …** `[VERIFIED ✓ — 2026-06-16,
  python-pptx 1.0.2: fresh paragraph.level == 0]`. So `paragraph.level = 1` applies the SECOND
  list-style level (`a:lvl2pPr`), not the first. When matching a template's bullet/number style by
  level, remember the API integer is one less than the human "level N" — off-by-one here silently
  applies the wrong bullet/indent.

## Hard traps (carried from defense ppt-edit experience)

- **Never edit in place.** Original is sacred. Write to `outputs/<slug>/current.pptx`; the source
  file is never mutated. (See version-snapshot policy below.)
- **Provenance lock**: before replacing any text, read and quote the original run first. Never
  invent replacement text (especially titles) — fabricated English titles is a logged regression.
- **Proofread ALL slides, not just changed ones.** A change on slide 5 can drop slide 1's title.
  Render every slide to PNG and Read them.
- **SmartArt / charts: do not edit in place → regenerate.** python-pptx cannot reliably mutate
  these; build fresh shapes instead.
- **Orphan slideMaster** triggers the PowerPoint "repair" dialog even when the file opens in
  soffice. Integrity check must catch dangling relationships and orphan masters (see verify card).
- **Unescaped `&` (or `<`) in injected text → repair dialog + render dropout** `[VERIFIED ✓ — 2026-05-28]`:
  when you build new run text yourself (not copied from an existing run), raw `&` / `<` / `>` break
  XML parsing. Symptom is twofold and easy to misread: (1) **PowerPoint shows the "repair" dialog**,
  and (2) **the paragraph containing the bad char — and everything after it in that shape — silently
  vanishes from the soffice render**. A wasted detour is to blame the missing paragraph on box height
  / `spAutoFit` clipping; it is not height, it is the parser stopping at the `&`. **Always escape new
  text**: `&`→`&amp;`, `<`→`&lt;`, `>`→`&gt;`. Runs copied from the original are already escaped — only
  hand-typed additions bite. Validate with `xml.etree.ElementTree.fromstring()` on the part before repackaging.
- **zip-update duplicate part → repair dialog** `[VERIFIED ✓ — 2026-05-28]`:
  running `zip deck.pptx ppt/slides/slideN.xml` **twice for the same path across separate commands**
  can leave **two entries for that part** in the archive. `unzip -t` (CRC) still passes, but OOXML
  forbids duplicate parts so PowerPoint demands repair. Replace each part **once per repackage**, or
  rebuild the whole zip clean. Detect with `collections.Counter(ZipFile(f).namelist())` — CRC alone
  will not catch it.
- **Repackage verify gate**: after any `zip`-update of a part, do NOT trust `unzip -t` alone. Run the
  full check: (1) CRC, (2) **no duplicate names**, (3) **ET.fromstring on every edited slide XML**,
  (4) `Presentation(file)` opens via python-pptx (same OPC parser class as PowerPoint), (5) edited
  parts still have `[Content_Types].xml` Overrides. Both repair-dialog traps above pass CRC but fail
  checks 2–4 — those are what actually predict the PowerPoint repair prompt.
- **AlternateContent (Choice/Fallback)**: a shape can have two XML representations; editing only
  one leaves them inconsistent. Inspect both branches.
- **Copied-shape namespace ghost → PowerPoint render dropout** `[VERIFIED ✓ — 2026-05-28]`:
  a shape pasted in from another deck can drag a **local namespace declaration onto its own `<p:sp>`
  root** (e.g. `<p:sp xmlns:a14="...">`) plus inline `extLst`/`a16:creationId`, while the slide root
  (`<p:sld>`) declares neither `a14` nor `mc`. The XML is otherwise valid — text, coords, color,
  `hidden`, cNvPr id all check out — yet **PowerPoint (Mac) silently skips that one shape at render
  time**. The body looks present on disk but is absent on the user's screen. This is the **inverse
  of the python-pptx false-negative** (there: text on disk, tool can't read it; here: text on disk,
  renderer won't draw it) and a cousin of the AlternateContent trap (different renderer fails).
  - **Diagnose**: dump every `<p:sp>` open tag and flag any carrying a local `xmlns:`; the offending
    shape is the lone one with it. Also compare `<a:rPr lang=...>` — a copied EN shape often carries
    `lang="ko-KR"` while its visible siblings use `en-US`.
  - **Fix**: rebuild the shape from a *visible sibling's* sp template on the same slide — strip the
    local `xmlns`, drop the inline `extLst`/`creationId`, set `lang="en-US"`, keep coords/font/text.
    Normalizing to the sibling shape resolves it regardless of which factor was the true culprit.
  - **Authority rule**: the user's PowerPoint screen is ground truth, NOT the disk render. If a
    shape is on disk but the user says it's invisible, do **not** argue the disk render is right —
    this trap is exactly why disk-present ≠ screen-visible. soffice may render it fine yet PowerPoint
    drops it, so a clean soffice PNG does not clear the trap; only the user's PowerPoint confirms.
- **Korean font**: set `Apple SD Gothic Neo` explicitly for KO text, or soffice substitutes and
  the PNG looks wrong.

## Formulas (inline / block math) — the gap ppt-* never closed

python-pptx 1.0.2 has **no math API**. Two paths were probed in T6 with a real .pptx rendered via
soffice → pdftoppm and the PNG read by eye (2026-05-28). Result below — do not re-guess.

### Path B — LaTeX → image embed  `[STATUS: VERIFIED ✓ — 2026-05-28]`  ← **default path**
Render the formula to a transparent PNG with matplotlib mathtext (no external LaTeX needed), then
add it as a picture shape. **Proven**: `\hat{x}_k = x_k + K_k(z_k - Hx_k)` rendered correctly in
soffice — superscripts, subscripts, hat all legible. Not natively editable afterward, but rendering
is guaranteed across soffice and PowerPoint. **Use this path for any deck that must survive the
soffice render/verify pipeline.**
```python
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig = plt.figure(figsize=(4, 1))
fig.text(0.01, 0.3, r"$\hat{x}_k = x_k + K_k (z_k - H x_k)$", fontsize=28)
fig.savefig("eq.png", dpi=300, transparent=True, bbox_inches="tight", pad_inches=0.1)
plt.close(fig)
# then: slide.shapes.add_picture("eq.png", left, top, height=Inches(1.0))
```

### Path A — native OMML injection  `[STATUS: soffice does NOT render — PowerPoint-only, NOT recommended]`
PowerPoint math is OMML (`<m:oMath>`) injected via lxml into the paragraph's `<a:p>`. **T6 finding**:
the OMML is written into the .pptx correctly, but **soffice/Impress renders it as a blank** — the
equation does not appear in the render/verify PNG (same class as the "GIF → soffice blank" trap).
PowerPoint proper may display it, but since OMD's verify gate renders through soffice, Path A
breaks verification. **Do not use Path A unless the deck is PowerPoint-only and you skip soffice
verification.** Prefer Path B.

**Rule**: a path is `VERIFIED ✓` only after an actual .pptx is generated, rendered via soffice,
and the equation is legible in the PNG (Read-confirmed). No guessing into this card. (Path A failed
exactly this test; Path B passed it.)

## Version-snapshot policy (binary files can't git-diff)

Layout is the fixed, deterministic structure in `references/output-layout.md` — the single
delivered copy lives in `outputs/`, all work-product (version copies, PNG renders, intermediates)
lives in the `.omd/` work area, so the output folder never bloats with snapshots:

```
outputs/<slug>/
└── current.pptx                         # the one delivered copy — always edit this

.omd/<slug>/                             # work area (Claude-facing; pruned at terminal)
├── versions/
│   ├── v01_YYYY-MM-DD_initial.pptx
│   └── v02_YYYY-MM-DD_<change-summary>.pptx  # snapshot taken JUST BEFORE a large edit
├── renders/current/slide-NNN.png        # PNG renders for proofreading (≥150 dpi)
├── gen-image/                           # generated diagrams/backgrounds (when used)
└── tmp/                                 # soffice/pdftoppm intermediates — disposable
```
- Version filename: `v{NN}_{YYYY-MM-DD}_{summary}.pptx`, `NN` zero-padded (v01, v02, … v10) so
  `ls` order = version order; `summary` is kebab-case, ≤ 30 chars.
- Snapshot only **before a large edit** (section add/remove, structural change, many slides
  affected) — not for a one-line text swap, which keeps the version count (and disk use) bounded.
- `doc-verifier` warns when `.omd/<slug>/versions/` exceeds a threshold → offer to prune.
- `versions/` snapshots and `renders/` PNGs are work-product, not deliverables: they stay out of
  `outputs/` and are cleaned at the end of the pipeline (see `references/output-layout.md` §5).
