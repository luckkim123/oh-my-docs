---
name: docs-standardize
description: |
  Inductively extract a common standard formatting ruleset from several existing documents — font, color, margin, and layout patterns
  into a single style spec. Not single-document extraction (ppt-analyze) but pulling the *common rules* across N documents to
  build an "our org/lab standard". Verifies spec accuracy via round-trip.
  Triggers: 양식 추출, 표준 양식, 우리 랩 발표 양식, 양식 규칙 뽑아, design system 추출,
  style spec, standardize, 공통 양식, 템플릿 규칙, 양식 통일,
  extract format, standard format, lab presentation format, extract design system, common format, template rules, unify format
---

# docs-standardize — Standard Format Extraction (Stage 2, optional)

<Purpose>
Analyze several existing documents to inductively extract the *common* standard formatting rules (font, color roles, margins, recurring layouts) and codify them into a single style spec. An evolution of ppt-analyze — inducing the common denominator across N documents rather than from one.
</Purpose>

<Use_When>
- Requests like "extract our lab/org presentation format rules" — define a standard from multiple samples
- When building a new document to match an existing house style (generate a spec for build to reference)
</Use_When>

<Do_Not_Use_When>
- When there is no existing document to reference → skip (build uses the default tone preset)
- When analyzing just a single document/page is enough → use doc-analyzer directly (no induction needed)
</Do_Not_Use_When>

<Gate>
**Gate — extraction scope + round-trip.** Confirm which documents count as the standard population → after extraction,
regenerate one representative page → compare PNGs against the original at ≥85% match. If below, reinforce the spec.
</Gate>

<Steps>
1. Confirm the standard population (several .pptx/.docx).
2. Dispatch doc-analyzer to each document, extracting each one's design system:
   `Task(subagent_type="oh-my-docs:doc-analyzer", ...)`
3. Induce the **common denominator** (fonts/colors/margins/layouts recurring across multiple documents) from the extraction results → style spec.
4. Round-trip verification: regenerate one representative page from the spec → compare against the original. If <85%, reinforce the spec.
5. Present the style spec as the gate → confirm.
</Steps>

<Output>
style spec (font, color roles, margins, recurring layout patterns) — the data that docs-build references to build "per this format".
Combined with the pitfall knowledge in references/formats/<format>.md for the builder to use.
</Output>
