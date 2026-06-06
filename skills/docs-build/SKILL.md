---
name: docs-build
description: |
  Produce the actual document from an approved outline — read the format knowledge card and drive the render
  engine (python-pptx/docx/hwpx) directly. Supports inline/block math. No in-place edits of the original (new file + version snapshot).
  OMD builds (rebuilds) directly without calling the existing ppt-* skills. OMD stage 4.
  Triggers: 만들어줘, 산출, 생성, 빌드, .pptx 만들어, .docx 만들어, 발표자료 생성,
  document build, generate document, 수식 넣어, 슬라이드 생성
---

# docs-build — Production (stage 4)

<Purpose>
Produce the actual .pptx/.docx/.hwpx from the approved outline. Read the references/formats/<format>.md card and drive the render engine directly — do not call the existing ppt-*  (OMD = rebuild). **Math** only via the path the card marks VERIFIED.
</Purpose>

<Use_When>
- The outline is approved and it is now time to produce the deliverable
- *Revising* an existing document (revision — work after taking a version snapshot)
</Use_When>

<Do_Not_Use_When>
- The structure is not settled yet → docs-plan first
- You only want a "how does it look?" review → docs-inspect
</Do_Not_Use_When>

<Gate>
**Gate 2 — content confirmation.** After building, show the builder's sanity render (PNG) to the user to confirm
the content is correct. (Not a craftsmanship judgment — that is inspect/verify.)
</Gate>

<Format_Knowledge>
Per-format tools, pitfalls, math, and version policy are the **single source of truth in the references/formats/<format>.md card**. Do not duplicate them into this skill/agent — read the card:
- pptx → references/formats/pptx.md (python-pptx, math = matplotlib PNG only [soffice does not render OMML], version snapshot)
- docx → references/formats/docx.md (python-docx, math 2 paths [OMML editable VERIFIED + matplotlib fallback], header/PAGE field/Korean-font pitfalls)
- xlsx → references/formats/xlsx.md (openpyxl/xlsxwriter routing, `<v>0</v>` formula-cache pitfall, structure-validation gate [not PNG read-through])
- hwpx → references/formats/hwpx.md (python-hwpx [pure Python, in-process], form filling 3-tier fallback [fill_by_path→`{{}}`→free text] = main, validation [HwpxDocument.validate() XSD + package-validation CLI], math = unsupported [v2, silently dropped on read], `.hwp` = normalization gate only, soffice hwpx render UNVERIFIED, import not measured on this machine)
</Format_Knowledge>

<Steps>
1. Dispatch doc-builder (pass the outline + the design system from analyzer/standardize):
   `Task(subagent_type="oh-my-docs:doc-builder", ...)`
2. The builder reads the card → (if a revision) snapshots to `.omd/<slug>/versions/` → build script → produce → math (VERIFIED path) → its own PNG sanity render (`.omd/<slug>/renders/current/`).
3. Present the deliverable (outputs/<slug>/current.<ext>) + sanity PNG at gate 2 → confirm.
</Steps>

<Output>
The final version the user sees is the single `outputs/<slug>/current.<ext>`. Version snapshots (for large revisions), sanity renders, and build notes go in the workspace `.omd/<slug>/` (`versions/`, `renders/current/`, `build-notes.md`). The path convention's SSOT is `references/output-layout.md`. Hand off to inspect/verify.
</Output>
