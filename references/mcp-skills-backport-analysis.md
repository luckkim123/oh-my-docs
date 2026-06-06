# MCP / Official-Skills Backport Analysis — oh-my-docs (omd)

omd's format cards (`references/formats/*.md`) and build discipline evolve by borrowing the proven patterns of the **external document-automation ecosystem** (Office MCP
servers + Anthropic official Agent Skills). When that ecosystem updates, we need a durable baseline to judge
*what changed and whether omd needs updating*. This document keeps that "diff baseline" self-contained. (sibling: `references/omc-backport-analysis.md` — OMC harness pattern backport.)

> **This document lives in the distributed plugin's references/, so it is independent of any personal environment.** External repos are
> recorded by public URL only; no machine-specific absolute paths or user data are embedded.

---

## §1. Survey snapshot (2026-05-31) — ecosystem landscape

### Conclusion: omd does not attach MCP (confirmed)

- The **backend engine of nearly every** Office MCP server surveyed **is python-pptx / python-docx / openpyxl** —
  MCP is a JSON-RPC wrapper around the very libraries omd already drives directly.
- omd drives the libraries directly via Bash from an agent within a single harness → layering MCP on top only adds IPC and server-startup
  overhead. The MCP upside ("distribution to multiple clients") does not apply to omd's own use case.
- Therefore **borrow the patterns only** (not a connection). This is consistent with omd's "drive the library directly" philosophy.

### Surveyed MCP servers (for reference — not adopted, patterns only)

| Format | Representative server | ★ | Engine | What omd took from it |
|:---|:---|:---|:---|:---|
| pptx | GongRzhe/Office-PowerPoint-MCP-Server | 1.7K | python-pptx | 11-module / 34-tool API taxonomy |
| docx | SecurityRonin/docx-mcp | — | direct OOXML manipulation | workaround design for what python-docx cannot do |
| docx | meterlong/mcp-doc | 186 | python-docx | preserving original styles when editing |
| xlsx | haris-musa/excel-mcp-server | 3.9K | openpyxl | reference for engine selection |
| convert | microsoft/markitdown | 132K | MarkItDown | Office→md intake (not adopted) |

⚠️ **None of the 8 MCP servers have native math (OMML/math) support** — omd's docx OMML path is the differentiator.

### ⭐ Anthropic official Agent Skills (github.com/anthropics/skills) — the real borrowing source

The official `pptx`/`docx`/`xlsx` skills are in the **same family** as omd (drive libraries directly via bash inside a VM).
They are source-available, so the code/patterns were compared directly. **But here is where they differ from omd**:
- New generation: pptx=**pptxgenjs (Node)**, docx=**docx-js (Node)**. Because omd drives python directly, the **Node
  engines are not borrowed**; only the safety rules, QA recipes, and XML-editing discipline are borrowed.
- Editing existing files: `unpack → XML edit → pack --original` (schema validation). omd builds directly with python-docx.

---

## §2. diff baseline (re-review when the ecosystem updates)

- **The official skills have weak CHANGELOGs** → on the next update, read the diffs of the *adopted* files in §3 below directly and
  judge whether to update the omd cards:
  - `skills/{pptx,docx,xlsx}/scripts/office/{pack,unpack,soffice}.py`
  - `skills/xlsx/scripts/recalc.py`
  - `skills/*/scripts/office/validators/*.py`
- **MCP servers**: not adopted, so no need to track. But if any MCP starts to **natively support math OMML**
  (currently none do), omd's differentiator shrinks, so re-evaluate then.

---

## §3. Adoption/exclusion mapping (Mn = internal work ID of this backport)

### Adopt — embedded in cards after empirical verification

| Mn | Source pattern | omd application (actual change) | Verification |
|:---|:---|:---|:---|
| M1 | official QA recipe `soffice→pdf→pdftoppm -jpeg` | docx/xlsx card render recipe = **`-jpeg`** (`-png` direct conversion renders only the first page = LibreOffice bug). pptx card also under review | adv holds |
| M2 | `office/soffice.py` headless env | docx/xlsx cards get the `SAL_USE_VCLPLUGIN=svp` + sandbox AF_UNIX socket LD_PRELOAD shim hint | source confirmed |
| M3 | `recalc.py` LibreOffice macro | xlsx card: actual formula value = `ThisComponent.calculateAll()` macro required. **`--convert-to` alone does not recalc** (measured: stays 0) | **measured PoC5b** |
| M4 | python-docx OMML injection pattern | docx card math path A = `etree.XSLT(mml2omml.xsl)` → `p._element.append`. **issue #320 unresolved, but omd verified the render via soffice directly** | **measured PoC1·2** |
| M5 | docx tracked-changes / paragraph-deletion discipline | docx card "editing existing docx" section: author=Claude, paragraph mark `<w:del/>`, comment.py exception | source confirmed |
| M6 | xlsx engine division of labor (openpyxl/xlsxwriter) | xlsx card routing rule = new=xlsxwriter, edit=openpyxl (chart-load-loss warning) | adv holds + measured |
| M7 | route_emit format catalog | **added xlsx format token** to `hooks/route_emit.py` (STAGE line + body). Added xlsx to the regression test `test_context_lists_formats` | 11/11 green |
| M8 | xlsx **financial-model authoring conventions** (color-coding/number-format/formula composition) | new xlsx card section "Financial-model authoring conventions": colors by cell role (blue=input / black=formula / green=cross-sheet link / red=external reference / yellow background=key assumption), number formats (year=text, negative=parentheses, 0=`-`, multiple=0.0x), the **"formulas in cells, no python hardcoding"** principle (positive rule for the M3 `<v>0</v>` trap), source comment when hardcoding, dictionary-reference sanity check | direct comparison with official SKILL (re-scanned 2026-06-01) |

> **2026-06-01 re-scan note**: directly fetched and compared the anthropics/skills live repo (docx/pptx/xlsx/pdf SKILL.md).
> Only **1 new adoption**, M8 — the rest are confirmed as already-adopted (M1~M7) or intentionally excluded (docx-js/pptxgenjs Node engines,
> markitdown, pptx OMML). The **pptx deck design rules** (dominance 60-70%, motif repetition, no title underline)
> are valuable but omd's pptx work routes through the mckinsey-pptx template, so they fall under that jurisdiction → on hold. The **pdf
> skill** (pypdf/pdfplumber/reportlab/OCR/forms) exists but omd treats pdf only as an *output-verification artifact*, so pdf *authoring*
> is out of domain → no new card created (reference the official pdf skill directly when needed).

### Exclude (with rationale)

| Pattern | Exclusion rationale |
|:---|:---|
| **Real MCP server connection** (all 8) | direct python-library drive is already that engine. Only adds IPC overhead (§1) |
| **pptxgenjs / docx-js (Node new generation)** | omd builds directly with python-pptx/python-docx. The Node runtime dependency is not borrowed |
| **`unpack→pack --original` pipeline** (new-generation path) | omd uses the rebuild approach (generate from scratch with python). The pack validation discipline is referenced as a pattern only when *editing existing docx* |
| **markitdown intake (Office→md)** | omd's doc-analyzer reads directly. No separate conversion dependency needed |
| **pptx native OMML (Path A)** | **empirically re-confirmed: soffice Impress renders blank** (PoC3). pptx math stays as matplotlib PNG |
| **Anthropic Files API / code-execution** | omd is a local harness. The Anthropic-server dependency is not borrowed |

---

## §4. Per-format math rendering — empirical matrix (omd-specific finding)

> "code runs ≠ soffice renders." Below is the 2026-05-31 result of actually generating .docx/.pptx → soffice → PNG and verifying by eye.

| Format | OMML (native) | matplotlib PNG | Card policy |
|:---|:---|:---|:---|
| **docx** (Writer) | ✅ renders (caveat: `\hat` accent misaligned, `\sum`/`\,` render as □ empty box) | ✅ | path A default + fallback |
| **pptx** (Impress) | ❌ blank (no body-text loss) | ✅ | matplotlib PNG only |

→ The key point is that **math policy differs per format**. Inserting OMML into pptx without knowing this produces blanks.

---

**Analysis snapshot**: 2026-05-31 · verification = 5 measured PoCs (`/tmp/omd_math_poc/`, non-persistent) + adversarial
workflow 9-agent · **isomorphic sibling**: `references/omc-backport-analysis.md` (OMC harness domain)
