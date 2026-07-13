# Format cards

Each format or genre has one knowledge card under `references/formats/` — the single
source of truth the builder and verifier agents read for that format's tools and gate.

| Card | Engine | Verify gate |
| --- | --- | --- |
| `pptx` | python-pptx 1.0.2 · soffice · pdftoppm · matplotlib+Pillow (formula path B) | soffice to pdftoppm (`-png`, >=150 dpi) render for visual proofread. |
| `docx` | python-docx 1.2.0 · soffice · pdftoppm · latex2mathml+lxml (formula path A) · matplotlib+Pillow (path B fallback) | soffice to pdftoppm (`-jpeg`, >=150 dpi, PDF-first) render for visual proofread. |
| `xlsx` | openpyxl 3.1.5 (read/edit existing) · xlsxwriter 3.2.9 (new/bulk write) · soffice (recalc) · pandas (optional) | Primary gate is structural assertions via openpyxl — sheet names, expected cells/ranges present, formula cells still hold formulas, no unexpected errors; render (JPEG) is secondary and optional. |
| `hwpx` | python-hwpx (read/fill/edit/create/validate, in-process) · soffice (render, unverified for hwpx import) · pdftoppm | `HwpxDocument.validate()` — XSD schema validation against the bundled OWPML schemas; package/OPC integrity is exposed at the CLI layer; the render step is conditional on soffice actually opening the file. |
| `repo-docs` | Markdown (no engine to install) · markdownlint-cli2 · lychee (optional, network-dependent) · python3 stdlib | Seven checks — required sections in preset order, internal links/anchors, markdownlint-cli2, fenced code blocks carry a language tag, CHANGELOG conventions, badge markdown well-formed, and a scan for unfinished-content markers. |
| `site` | MkDocs 1.6.1 + Material 9.7.6 (via `uvx`) · markdownlint-cli2 · lychee (optional) · python3 stdlib | Five checks — `mkdocs build --strict` (with the card's `validation:` block present), markdownlint-cli2, internal links/anchors, built-HTML fresh-read, and nav completeness. |

Engine-missing rule: a required engine that is not installed yields the verdict
"UNVERIFIED (engine unavailable)" for that item — never a silent pass, never a fail on
the environment.
