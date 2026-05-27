# Evaluation Rubric — PPTEval 3 axes

> **What this is**: A shared rubric data file. `doc-inspector` uses it for *formative* critique
> (improvement suggestions, mid-work) and `doc-verifier` uses the Coherence/Design axes as part of
> its *summative* pass/fail gate. Source: PPTEval (PPTAgent, arXiv 2501.03936).

## The 3 axes

### 1. Content
Is the substance right?
- Each slide carries one clear message; no slide is a wall of text.
- Claims are supported (data / figure / citation) where they need to be.
- No placeholder text left in (`[Insert ...]`, `TODO`, lorem ipsum).
- Density within limits — KO title ≤ 50 chars, body ≤ 6 words/line (EN: 70 / 10). Defense/academic
  tone matches the audience.

### 2. Design
Does it look right?
- Consistent fonts (KO → Apple SD Gothic Neo), color roles, and margins across slides.
- No text overflow, no labels clipped off the slide, no overlapping shapes (check at ≥150 dpi —
  low-res renders hide overlap).
- Figures/tables legible at presentation size; aspect ratios sane (16:9 / 4:3 / 1:1).
- Alignment and whitespace deliberate, not accidental.

### 3. Coherence
Does it flow?
- Narrative arc holds (e.g. defense: research question → contribution → method → experiment →
  conclusion). Each slide follows from the last.
- Section transitions exist and are signposted.
- Title, agenda, and body are mutually consistent — no orphan section promised but never delivered.

## How the two reviewers use this

| | doc-inspector (formative) | doc-verifier (summative) |
|:---|:---|:---|
| When | mid-work, still fixable | right after build, before "done" |
| Output | ranked improvement list per axis | pass/fail + integrity gate |
| Axes | all 3, as suggestions | Design + Coherence as checks; Content completeness via spec |
| Stance | "here's how to make it better" | "this does / does not meet the bar" |

**Separation rule**: the inspector never declares a deck "done"; the verifier never just lists
nice-to-haves. Formative ≠ summative — and neither may be the same agent that authored the deck
(no self-approval).
