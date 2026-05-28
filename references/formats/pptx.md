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
| `soffice` (LibreOffice) | .pptx → .pdf for rendering | ✓ `/opt/homebrew/bin/soffice` |
| `pdftoppm` | .pdf → .png (visual proofread) | ✓ `/opt/homebrew/bin/pdftoppm` |
| `matplotlib` 3.9.4 + `Pillow` 11.3 | LaTeX math → PNG (formula path B) | ✓ installed |

**Render-to-PNG recipe** (used by verify/inspect for proofreading):
```bash
soffice --headless --convert-to pdf --outdir <dir> <deck.pptx>
pdftoppm -png -r 150 <deck.pdf> <dir>/slide   # ≥150 dpi — low dpi hides overlap
```

## Hard traps (carried from defense ppt-edit experience)

- **Never edit in place.** Original is sacred. Write to `outputs/<doc>/current.pptx`; the source
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

```
outputs/<doc-name>/
├── current.pptx                         # the working copy — always edit this
├── versions/
│   ├── v1_YYYYMMDD_initial.pptx
│   └── v2_YYYYMMDD_<change-summary>.pptx # snapshot taken JUST BEFORE a large edit
├── thumbnails/                          # PNG renders for proofreading
└── manifest.json                        # {version, timestamp, summary} history
```
- Snapshot only **before a large edit** (not for a one-line text swap — avoids the 12 GB bloat
  that buried the defense folder in PPT copies).
- `doc-verifier` warns when `versions/` exceeds a threshold → offer to prune old versions.
- ⚠️ This workspace syncs via iCloud; `versions/` copies sync too. Keep the user aware of size.
