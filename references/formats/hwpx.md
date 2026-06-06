# Format Knowledge Card — hwpx

> **What this is**: A data file, not a skill. The OMD agents (`doc-builder`, `doc-verifier`,
> `doc-inspector`) read this card to know the tools, traps, and verified techniques for the
> Korean office format. Borrow the engine (`python-hwpx` / soffice); the orchestration brain lives
> in the agents and stage skills. Do not duplicate this knowledge into agent files — point at this
> card. Sibling cards: `pptx.md`, `docx.md` (same discipline, different renderer + math behavior).

## Format reality

- **`.hwpx`** (newer, OWPML = ZIP + XML, the same family as OOXML) — readable / writable / editable
  on macOS/Linux/Windows via **`python-hwpx`** (pure Python, lxml-based, in-process). **This is the
  default path** — no Hancom Office, no Windows COM, no MCP/subprocess boundary.
- **`.hwp`** (older v5 binary, OLE compound file) — **cannot be written in pure Python.** Handle
  `.hwp` input only as a **normalize-to-hwpx/docx conversion gate** (manual Hancom export, or a
  conversion tool), never direct write. See `docs-convert` / `references/conversions.md`.

## Engine

| Tool | Role | Verified |
|:---|:---|:---|
| `python-hwpx` (PyPI `python-hwpx`, import `hwpx`, Apache-2.0, Py3.10+, lxml≥4.9) | read / fill / edit / create / validate `.hwpx`, in-process | `[VERIFIED: PyPI 2.9.1 published; API cross-checked against airmang/python-hwpx `src/hwpx/document.py` + README, 2026-05-31]` — install with `pip install python-hwpx`. ⚠️ **NOT yet import-tested on this machine** (the local Xcode-bundled python3 pip returned "No matching distribution" — an environment/index issue, not package absence; PyPI hosts 2.9.1). A `doc-builder` run must `pip install python-hwpx` into its own interpreter and confirm `import hwpx` before claiming a build. |
| `soffice` (LibreOffice) | `.hwpx` → `.pdf` for render proofread | `[UNVERIFIED]` — LibreOffice's hwpx import is incomplete; **confirm it actually opens the file before relying on a render gate** (resolve `command -v soffice` at run time) |
| `pdftoppm` | `.pdf` → image (visual proofread, *if* soffice renders hwpx) | resolve on PATH |

> **treesoop/hwp-mcp = pattern only, ZERO code.** A TS/Node/WASM MCP server (`@rhwp/core` Rust read +
> `jszip`+regex write). We borrow **only the design knowledge** — the 3-tier placeholder fallback
> idea, the tool-surface catalogue (what fill/cell/row/image operations an agent needs), OWPML
> structure understanding. The actual engine is `python-hwpx`, which has zero code lineage with
> treesoop. Never import or transliterate treesoop's regex-substitution code — its four weaknesses
> (regex XML substitution, text-node boundary mismatch, fragile nested tables, no post-write
> validation) are exactly what `python-hwpx`'s OWPML DOM + validation gate structurally avoid.

> **Cross-platform tool resolution**: never hardcode a binary path — resolve at run time
> (`command -v soffice`/`command -v pdftoppm`; Windows `where`). If absent, stop and tell the user how
> to install — do not silently skip a gate.

## Hard traps

- **Never edit in place. `.hwp` input is never written directly.** Original is sacred — write to
  `outputs/<slug>/current.hwpx`, source never mutated. Enforce `src != dst`. A `.hwp` (binary) input
  is a **convert gate only**, never a write target.
- **Provenance lock**: before replacing any text, read and quote the original run first. Never invent
  replacement text (fabricated content is a logged regression — same rule as pptx/docx).
- **Split runs**: a single visual word can be fragmented across multiple `<hp:run>`/`<hp:t>` nodes
  (style boundaries, IME composition). A naive "find this substring" can miss text split across runs.
  `python-hwpx`'s run-aware helpers (`replace_text_in_runs`, `find_runs_by_style`) handle this — use
  them, do not hand-roll string matching over raw XML (that is the treesoop text-node-boundary trap).
- **Formulas are silently dropped on read** (see Formulas below) — a document that "extracted fine"
  may have lost equations. Never claim a faithful read of a math-bearing `.hwpx`.
- **soffice hwpx render is UNVERIFIED** — do not assume the verify gate's render step works for hwpx
  the way it does for docx/pptx. Confirm soffice opens the specific file first; if it can't, fall
  back to the structural validation gate (below) and say the visual proofread was not possible.

## Form filling — 3-tier auto-detect fallback (MAIN use case)

Korean office forms (공문서, official documents) are the primary target. The user hands you a form; OMD **detects the
fill mechanism at run time** (no need to pre-declare it). Detection is OMD's job; substitution is the
library's. Log which tier was taken.

- **Tier 1 — cell-label based (`fill_by_path`)** ⭐ primary
  The "label cell + adjacent input cell" pattern of Korean documents. Fill by label-relative position,
  e.g. `{"성명 > right": "홍길동"}`. Probe with `find_cell_by_label` first — if labels exist, take this
  path. `fill_by_path` returns `applied_count` / `failed_count` → **report immediately what did NOT
  get filled** (never claim a clean fill if `failed_count > 0`).
- **Tier 2 — explicit placeholder (`{{name}}`)**
  If tier-1 label matching is thin, scan the body via `export_text` for `{{...}}` tokens → replace via
  `replace_text_in_runs` (run-aware, survives split runs).
- **Tier 3 — free-text substitution**
  Only when neither above exists. **Dangerous** — always report the change locations and count; if more
  matches change than expected, warn and stop rather than mass-replace silently.

## Create / read paths

### Read (lowest verification burden — implement first)
- `export_markdown` (LLM consumption), `export_text` (raw text), `export_html` (render approximation).
- Tables → markdown. Images / footnotes / headers-footers within library support.
- **Equations are dropped** (Formulas, below) — the markdown/text export does not descend into
  `<hp:equation>`. Flag any math-bearing document as "math lost on read".

### Create (highest verification burden — implement last, gate-required)
- `HwpxDocument.new()` → `add_paragraph` / `add_table` / `add_image` / `add_section` /
  `set_header_text` / `set_footer_text` → `save_to_path`.
- Tables/images are emitted as real OWPML (not flattened text). **Cannot claim "created" until the
  validation gate (below) passes.**

## Validation gate (`docs-verify` hwpx branch)

`python-hwpx` ships validation — OMD calls it rather than writing its own:
- **`HwpxDocument.validate()`** — runs XSD schema validation on the current document state against
  bundled OWPML schemas (`hwpx.tools._schemas/*.xsd`). The hwpx analogue of pptx's orphan-master
  check. `[VERIFIED: method present in document.py — 2026-05-31]`
- **Package / OPC integrity** (mimetype STORE entry, dangling rels — analogue of pptx/docx
  dangling-relationship checks) is exposed at the **tools/CLI layer**, not as a `HwpxDocument`
  method. CLI commands installed with the package: `hwpx-validate`, `hwpx-validate-package`,
  `hwpx-analyze-template`, `hwpx-text-extract`, `hwpx-page-guard`.
  ⚠️ `[UNVERIFIED on this machine — confirm exact CLI/import name at build time]` — the design
  referenced `validate_document`/`validate_package`; the GitHub source shows a single
  `HwpxDocument.validate()` for the in-process path. Resolve the precise package-validation entry
  point (CLI `hwpx-validate-package` vs a `hwpx.tools` function) when `doc-builder` first wires this.
- **Render gate is conditional**: try `soffice --headless --convert-to pdf` → `pdftoppm` only after
  confirming soffice opens the hwpx. If soffice can't render hwpx on this machine, the structural
  validators above ARE the gate — say so; do not silently skip and do not claim a visual proofread
  you didn't do.

## Formulas — UNSUPPORTED (v2 candidate)  `[STATUS: VERIFIED unsupported — 2026-05-31]`

`python-hwpx` has **no equation support**. Verified in code, not guessed:
- No equation class, builder, fixture, or example (grep 0 hits).
- `export_text`/`export_markdown` do **not** descend into `<hp:equation>` → math is **silently
  omitted** on read.
- No `add_equation` / write API for math.
- Hancom's equation script is **not LaTeX** ("Equation Version 60", OWPML `EquationType` carries a
  `<script>` child with Hancom's own syntax).
- Only workaround: `ObjectFinder(tag="equation")` + raw `GenericElement.text` to hand-extract the
  Hancom script string at the XML level — **unvalidated, not a library feature**. Do not present it as
  supported.

**Rule**: if a deliverable requires equations, hwpx is **not** the right output path in v1 — say so
and offer docx (path A OMML, VERIFIED) instead. Mark equation work as v2.

## Version-snapshot policy

Same layout as the pptx/docx cards: the one delivered `outputs/<slug>/current.hwpx`, with version
snapshots and renders in the `.omd/<slug>/` work area (`versions/`, `renders/`, `tmp/`). Snapshot only
before a large edit. See `references/output-layout.md` for the fixed structure and naming.

## Implementation order (verification difficulty ascending)

1. **Read** (Hancom-produced valid doc → lowest burden) — confirm `export_markdown` works.
2. **Form fill** (main; replace text only in a valid doc) — `fill_by_path` 3-tier fallback.
3. **Validation gate** (`validate_document` / `validate_package` wired) — gate before create.
4. **Create** (assemble empty doc → highest burden) — gate-required.
5. **Formulas** = honestly "unsupported / v2".
