# Format Knowledge Card — docx  `[STATUS: STUB — full card after pptx pilot]`

> Data file for OMD agents. Borrow the engine (`python-docx` + soffice), brain stays in agents.
> This is a stub: the MVP pilots `pptx`. Fill in when the docx build path is implemented.

## Engine (planned)
| Tool | Role | Status |
|:---|:---|:---|
| `python-docx` | styles, sections, tables | NOT installed (2026-05-28) — `pip install python-docx` when needed |
| `soffice` | .docx → .pdf render | ✓ available |

## Known traps to capture later
- **Page-number fields** are easy to break — editing the field run can wipe the auto-number.
- **First-page header** is not reachable via the normal header collection (separate property).
- **Never edit in place** — same rule as pptx. Write `outputs/<slug>/current.docx`.

## Formulas
- python-docx has **no math API** (same gap as pptx). OMML `<m:oMath>` lives in `<w:p>`; inject via
  `docx.oxml.OxmlElement` directly. Path B (matplotlib image) also applies. Prove before relying.

## Version-snapshot policy
Same layout as the pptx card: the one delivered `outputs/<slug>/current.docx`, with version
snapshots and renders in the `.omd/<slug>/` work area (`versions/`, `renders/`, `tmp/`). See
`references/output-layout.md` for the fixed structure and naming.
