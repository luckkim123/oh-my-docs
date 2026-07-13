---
name: docs-learn
description: "Heavy channel: promote candidate style defaults from the observation ledger (.omd/learned.md) into the project's durable style-spec (.omd/wiki/convention/lab-style-spec.md), through a human gate. doc-inspector judges (read-only), the human approves, this skill records. Document content is never a promotion target."
triggers:
  - "this kind of deck always ~"
  - "always include"
  - "this org's default"
  - "promote default"
  - "learned.md promote"
  - "docs-learn"
---

# docs-learn — observation → style default promotion (heavy channel, human gate)

> **Role**: review the candidate observations (`OBS` blocks) accrued in `.omd/learned.md`, and
> promote only those that satisfy the repetition/stability/non-contradiction criteria **and are
> human-approved** into the project's **durable style-spec** — the `.omd/wiki/convention/lab-style-spec.md`
> the `wiki/README.md` contract defines (per-project, gitignored, the place `docs-standardize`'s
> otherwise session-volatile spec becomes a persisted "lab standard"; a `<style-key>` may live in
> a sibling `.omd/wiki/convention/<key>-style-spec.md`). The document-domain analogue of omp-learn.
> **Document content — text, claims, numbers, sources — is permanently off-limits for promotion.**

## Purpose

The promotion stage of the **heavy channel**: the longer omd is used, the more its style defaults
harden to *this* user / *this* deck type. Unlike the light channel (wiki auto-append), a value
changed here becomes an **enforced standard** for later plan/build/verify, so it must pass a
human gate.

## Use when / Do not use when

**Use when**:
- `status: candidate` observations have accrued in `.omd/learned.md` and the user wants to promote.
- the user explicitly stated a rule ("this kind of deck always uses 12pt captions") — that is
  `user_stated`, where evidence 1 suffices, but the gate still applies.

**Do not use when**:
- a request to promote document content (text, a claim, a number, a source) → **reject**
  (content-preservation, permanently off-limits — `learning-protocol.md` §6.F).
- an observation seen only 1–2 times that is not `user_stated` → not yet promotable (need ≥3 or `user_stated`).
- auto-promotion without user approval → **forbidden** (heavy-channel invariant).

## Execution policy (core)

1. **Human gate is absolute**: even if doc-inspector judges a candidate "promotable", nothing is
   written without explicit human approval.
2. **AND criteria**: promotion requires (repetition ≥3 OR user_stated) AND counter_examples 0
   AND not user_overridden AND stable AND non-contradicting. Any one failing → hold.
3. **user_stated exception**: a rule the user stated directly needs only evidence 1 (bypasses ≥3),
   but still passes the human gate.
4. **scope**: record as `global` (universal habit) vs `<style-key>` (this deck-type only). Never
   promote across the wrong scope.
   - ⚠️ **Two different "global" axes — do not conflate.** This `scope: global` is a *style-spec
     applicability* label (the default applies to every deck-type, vs one `<style-key>`). It is a
     **different axis** from the wiki's local↔global *storage-location* tier in §4b below. A rule
     can be `scope: global` yet still live only in the *local* `.omd/wiki/`, and vice-versa.
4b. **local→global wiki promotion (separate path, the storage-location axis)** — distinct from the
   `scope` label above, light-channel assets may be promoted by *physical storage location* from
   the local `.omd/wiki/` up to the *parent folder's `.omd/wiki/`* (the global tier, found by
   ascent — `references/wiki/README.md`). At a project's end, a reusable asset (`pattern/`
   disposition, `convention/` org-or-type form rule, `decision/`) may, **after human approval**, be
   copied to the ancestor `.omd/wiki/<category>/`. Rules:
   - Only *document-agnostic reusable* form assets rise — this project's own defect quirks stay local.
   - ⚠️ **content (text·claims·numbers·sources) is permanently forbidden from the global tier**
     (heavy or light — `learning-protocol.md` §6.F·§1.4), the omd analogue of oms's citation-safety.
   - ⚠️ **cross-project confidentiality scrub (omd-specific)**: the global tier is shared by multiple
     document projects that may hold confidential material, so a promoted note must carry only the
     **abstracted form rule** ("captions are 12pt black"), never a **project-identifiable** detail
     (client name, internal codename, confidential path). "The ACME deck uses red captions" stays
     **local**. Scrub identifiers before any global copy (`learning-protocol.md` §1.4·§6.F).
   - Human gate required — no auto-promotion. `pattern/` stays permanently light even at the global
     tier (recalled, never enforced). If there is no ancestor `.omd/`, advise the user to init one
     in the documents' parent folder (never create it in the parent/home unasked).
5. **judgment ≠ approval**: doc-inspector only *judges* (read-only); only a human *approves*. No
   self-approval in the same context.

## Steps

1. Read `.omd/learned.md`, collect `status: candidate` observations.
2. Delegate each candidate to `oh-my-docs:doc-inspector` for promotion-eligibility judgment (read-only):
   - `Task(subagent_type="oh-my-docs:doc-inspector", ...)` to review each OBS's repetition,
     counter-examples, stability, and contradiction.
3. Present only inspector-eligible candidates to the user as a **GATE**:
   - OBS-id, pattern, proposed change (which style-spec / style-key field → what value),
     evidence, scope.
4. For approved candidates only:
   - update the default in `.omd/wiki/convention/lab-style-spec.md` (or, for a `<style-key>` scope,
     the sibling `.omd/wiki/convention/<key>-style-spec.md`). This is a *durable* default in the
     work area — NOT the plugin repo (heavy-channel data lives in `.omd/`, per the wiki contract).
     When creating or updating a style-spec file, validate the target with
     `query_helper.safe_wiki_path()` and derive any NEW filename via
     `query_helper.title_to_slug()` (KN-3·KN-4).
   - update the `specificity` / `origins` / `learned_refs` meta (per `learning-protocol.md` §4 formula).
   - mark the OBS `status: candidate→promoted`, record `promoted_to`.
5. Rejected candidates → `status: rejected` + reason.
6. **(optional) local→global wiki promotion** — if a just-promoted (or already-local) light asset
   is reusable across documents (§4b), present it at the **same human gate**: "copy this to the
   global `.omd/wiki/` (parent folder, reused by every project)?". On approval, scrub project
   identifiers + verify content 0, then copy to the ancestor `.omd/wiki/<category>/`. No ancestor
   `.omd/` → advise, do not auto-create. Skipped silently if nothing is reuse-worthy.
   Validate the ancestor-tier target with `query_helper.safe_wiki_path()` before the copy
   (the filename already exists locally — no new slug needed).

## Output

```
DOCS-LEARN: <N candidates reviewed>
─ inspector-eligible: <OBS-id list>
─ GATE pending: <items needing user approval>
─ (after approval) promoted: <OBS-id → style-spec.field = value>
─ specificity: <key>: <before>→<after>
─ rejected: <OBS-id + reason>
```

## Content preservation (invariant)

- A document's *content* — text, claims, numbers, sources — is **permanently off-limits for
  promotion**. These are the document's own substance, not a style default.
- If a content-targeting `candidate_default` appears in learned.md, doc-inspector auto-rejects it.
- omd learns FORM, never content (`learning-protocol.md` §6.F). This is the omd analogue of oms's
  citation-safety, and it is absolute.

## Notes

- inspect (formative) · verify (summative) · learn (promotion) are three separate stages. learn
  is heavy-channel only.
- same philosophy as omp-learn: observation → human gate → enforcement. Only the domain (document
  form) differs.
