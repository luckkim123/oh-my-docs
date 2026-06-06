---
name: docs-convert
description: |
  Document format / deliverable conversion stage — .pptx/.docx→distribution PDF, .md→docx, .hwp→hwpx normalization gate.
  It only orchestrates render engines (soffice/pandoc); it does not write a new converter. Uses verified paths only,
  flags the unverified explicitly. Stage-centric (format is a variable).
  Triggers: PDF로 변환, 납품본, 변환해줘, pptx를 pdf로, hwp 변환, 포맷 바꿔,
  convert document, export pdf, to pdf, 배포용
---

# docs-convert — format/deliverable conversion (stage)

<Purpose>
Convert a finished document into another format or deliverable. .pptx/.docx → distribution PDF, .md → docx, .hwp → hwpx normalization. It does not write a new converter; it orchestrates verified engines (soffice/pandoc) — references/conversions.md is the single source of truth for which conversions are verified.
</Purpose>

<Use_When>
- Exporting a finished deck/document to a distribution PDF
- Normalizing a .hwp input into hwpx/docx that OMD can handle (conversion gate)
- Promoting a .md draft to .docx
</Use_When>

<Do_Not_Use_When>
- If you are *creating* a new document → docs-build
- If you want to directly *edit/write* a .hwp → not possible (macOS pure-Python limitation). Normalization gate only.
</Do_Not_Use_When>

<Conversion_Knowledge>
references/conversions.md = single source of truth for the conversion matrix. Use only after checking the verification status (VERIFIED/UNVERIFIED/GATE):
- **.pptx → .pdf** = VERIFIED ✓ (soffice). Default path for deliverables.
- **.hwp → hwpx/docx** = GATE (not possible with macOS pure Python, manual export). Direct writing prohibited.
- Everything else is UNVERIFIED — on first use, run the actual conversion + verify the output, then update the matrix.
</Conversion_Knowledge>

<Gate>
**Gate — conversion check.** After conversion, confirm the output file exists + has a non-trivial size. For a PDF, eyeball content preservation by rendering the first page to PNG. Never mutate the original (write to outputs/<slug>/ under the new extension).
</Gate>

<Steps>
1. Check the requested conversion's status in references/conversions.md. If GATE/not possible, notify the user and stop.
2. Dispatch doc-builder (conversion = driving an engine, so it is the builder lane):
   `Task(subagent_type="oh-my-docs:doc-builder", ...)`  — state "convert, not author" explicitly.
3. The builder converts via the verified path → confirm the output file exists + its size.
4. (PDF) Confirm content preservation by rendering the first page → present the gate.
5. If this is a newly verified conversion, update the conversions.md matrix (VERIFIED ✓).
</Steps>

<Output>
outputs/<slug>/<name>.<new-ext> + a conversion note (engine/exit/size). Original preserved. (Conversions/deliverables are a separate output family from `current.<ext>` — keep them in the same outputs/<slug>/ folder as new-extension files, but do not overwrite the build artifact `current.<ext>`.)
</Output>
