# Evaluation Rubric — site axes

> `doc-inspector` uses this card formatively (improvement points, ranked). `doc-verifier`
> does NOT read this card — the mechanical axes live in the site card's verify gate
> (`references/formats/site.md`). Dimension frame source: **Diátaxis** (diataxis.fr) —
> the quadrant model supplies the information-architecture axis.

## Axis split (who checks what)

| Axis | Nature | Checked by |
|:---|:---|:---|
| Build & link integrity (strict build, lint, internal links/anchors, nav completeness) | mechanical | site card verify gate ①②③⑤ — never an inspector lens |
| Information architecture | qualitative | inspector lens 1 |
| Prose quality | qualitative | inspector lens 2 |

## Lens 1 — Information architecture

- Diátaxis coverage: does each quadrant exist, and does each page serve exactly ONE
  quadrant? (a tutorial that drifts into reference is the classic failure)
- nav shape: top level mirrors the quadrants; depth ≤ 2; two-click reachability to any page.
- Entry flow: does index.md route each audience to the right quadrant in one hop?

## Lens 2 — Prose quality

- Style-guide adherence (pick one voice; consistent person/tense; sentence length sanity).
- Quadrant-appropriate register: tutorials speak in guaranteed steps, reference stays dry
  and complete, explanation argues trade-offs — register bleed is a finding.
- Vale is the optional mechanical assist here (not installed → note it, D3 spirit); the
  lens itself is judgment, not lint.

## Lens composition rule (PS-3)

The inspector runs exactly the qualitative axes above — for site that is **2 lenses**
(build/link integrity is already mechanical in the verify gate). Composition is per-genre
and fixed by the rubric card; the skill body never hardcodes a lens list.

## How the two reviewers split

Same rule as ppteval and repo-docs: the builder never inspects its own output as the
inspector, and the inspector never issues the verdict — **no self-approval** anywhere in
the lane. Verifier = mechanical gate + fresh evidence; inspector = these lenses.
