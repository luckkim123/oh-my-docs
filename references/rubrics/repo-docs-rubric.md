# Evaluation Rubric — repo-docs axes

> **What this is**: the repo-docs sibling of `ppteval.md`. `doc-inspector` uses it for
> *formative* critique; `doc-verifier` does NOT use this file — every mechanical axis for
> this genre already lives in the card's verify gate (`references/formats/repo-docs.md`).
> This rubric holds ONLY the qualitative axes (PS-3: lens composition = the axes verify
> does not check mechanically).
> Dimension frame source: Treude et al.'s ten-dimension documentation-quality framework
> (the original source — do not cite a "7-axis" scheme; none exists in the LintMe paper).

## Axis split (who checks what)

| Axis | Nature | Checked by |
|:---|:---|:---|
| Section presence/order, links, dates, badges, placeholders | mechanical | card verify gate ①②⑤⑥⑦ |
| Lint / code-fence language tags | mechanical | gate ③④ |
| **Welcoming onboarding** — does the opening tell a newcomer what this is, why it matters, and how to start, within 30 seconds? | qualitative | inspector lens 1 |
| **Information scent** — can a reader route to install / usage / contributing without reading everything? Is disclosure progressive (short top, detail below)? | qualitative | inspector lens 2 |
| **Honesty & maintenance signals** — does it promise only what the repo actually does? Stale sections, aspirational claims, dead ceremony? | qualitative | inspector lens 3 |

## Lens composition rule (PS-3)

The inspector runs exactly the qualitative axes above for this genre. Composition is
per-genre and fixed by the rubric card — office decks run PPTEval's 3 axes
(`ppteval.md`), repo-docs runs these 3 lenses. The skill body never hardcodes a lens list.

## How the two reviewers split

Same separation as `ppteval.md`: the inspector never declares "done" (formative), the
verifier never lists nice-to-haves (summative), and neither may be the context that
authored the set — no self-approval.
