# Produce and verify a document

A recipe for turning a brief into a verified deliverable using the `docs-pilot`
orchestration skill, which walks the full brief-to-document flow with a user gate at
each step.

## Recipe

1. Hand `docs-pilot` your brief. It drives `docs-intake`, `docs-standardize`,
   `docs-plan`, `docs-build`, `docs-inspect`, and `docs-verify` in sequence, pausing
   for your approval at each step.
2. `docs-inspect` gives formative feedback — improvement points, not a verdict.
3. `docs-verify` is the summative gate — deterministic, exit-code first. It is a
   separate lane from `docs-inspect` by design: no self-approval.

## Checking the verify gate

Each format or genre's verify gate lives in its own knowledge card under
`references/formats/`. Two examples:

- **repo-docs** (`references/formats/repo-docs.md`): seven checks — required sections
  present in the preset order, internal links/anchors resolve, markdownlint-cli2
  passes, every fenced code block carries a language tag, CHANGELOG date/version/type
  conventions, badge markdown is well-formed, and a scan for unfinished-content
  markers.
- **site** (`references/formats/site.md`): five checks — `mkdocs build --strict` (with
  the card's `validation:` block present), markdownlint-cli2 passes, internal
  links/anchors resolve, a fresh read of the built HTML, and nav completeness (every
  `docs/**.md` listed in `nav:`).

Every borrowed-engine run's stdout and stderr is captured to
`.omd/<slug>/verify-runs/<engine>-<timestamp>.log`.
