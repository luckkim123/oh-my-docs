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
**Gate 2 — content confirmation.** After building, show the builder's sanity evidence to the user —
office formats: the sanity render (PNG); text genres: a fresh-read of the produced files (site: the
built HTML) — to confirm the content is correct. (Not a craftsmanship judgment — that is inspect/verify.)
</Gate>

<Format_Knowledge>
Per-format tools, pitfalls, math, and version policy are the **single source of truth in the references/formats/<format>.md card**. Do not duplicate them into this skill/agent — read the card:
- pptx → references/formats/pptx.md (python-pptx, math = matplotlib PNG only [soffice does not render OMML], version snapshot)
- docx → references/formats/docx.md (python-docx, math 2 paths [OMML editable VERIFIED + matplotlib fallback], header/PAGE field/Korean-font pitfalls)
- xlsx → references/formats/xlsx.md (openpyxl/xlsxwriter routing, `<v>0</v>` formula-cache pitfall, structure-validation gate [not PNG read-through])
- hwpx → references/formats/hwpx.md (python-hwpx [pure Python, in-process], form filling 3-tier fallback [fill_by_path→`{{}}`→free text] = main, validation [HwpxDocument.validate() XSD + package-validation CLI], math = unsupported [v2, silently dropped on read], `.hwp` = normalization gate only, soffice hwpx render UNVERIFIED, import not measured on this machine)
- repo-docs → references/formats/repo-docs.md (GitHub repository document set genre — plain Markdown + borrowed linter chain [markdownlint-cli2 for the lint gate, lychee optional], artifact-set layout [outputs/<slug>/current/ + .omd/<slug>/manifest.json], 7-item deterministic verify gate, no PNG render — fresh-read instead)
- site → references/formats/site.md (MkDocs+Material static docs site genre — source artifact-set [mkdocs.yml + docs/ tree in outputs/<slug>/current/], built HTML is derived and goes to .omd/<slug>/site-build/ [never inside current/], machine gate = mkdocs build --strict with the card's validation block, Diátaxis structure frame, no PNG render — built-HTML fresh-read instead)
- no-reference fallback → office formats: references/themes/ (10 font/color presets — only when standardize was skipped for lack of reference documents; an induced style spec always wins over a preset). Text genres never fall back to themes/ — their card defines the fallback (repo-docs: genre section presets; site: the mkdocs-material palette schema) (F8)
</Format_Knowledge>

<Steps>
1. Dispatch doc-builder (pass the outline + the design system from analyzer/standardize):
   `Task(subagent_type="oh-my-docs:doc-builder", ...)`
2. The builder reads the card → (if a revision) snapshots to `.omd/<slug>/versions/` → build script → produce → math (VERIFIED path) → its own sanity evidence (office: PNG render into `.omd/<slug>/renders/current/`; text genres: fresh-read — site builds into `.omd/<slug>/site-build/`). Artifact-set rebuild: before overwriting files under `current/`, run the ownership guard — `references/output-layout.md` §3.4 (manifest check; unlisted/hash-drifted → AskUserQuestion).
3. Present the deliverable (single-file: outputs/<slug>/current.<ext>; artifact-set: outputs/<slug>/current/) + the sanity evidence (office: PNG; site: built-HTML fresh-read) at gate 2 → confirm.
</Steps>

<Output>
The final version the user sees is the single `outputs/<slug>/current.<ext>` (single-file formats) or the `outputs/<slug>/current/` artifact-set directory (text genres). Version snapshots (for large revisions), sanity renders, and build notes go in the workspace `.omd/<slug>/` (`versions/`, `renders/current/`, `build-notes.md`). The path convention's SSOT is `references/output-layout.md`. Hand off to inspect/verify.
</Output>
