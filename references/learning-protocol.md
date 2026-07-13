# Learning Protocol — omd's generic→specialized self-evolution (SSOT)

This card is the single source of truth for **how omd gets smarter about *this user/org's
document style* the more it is used**. It is the omd-domain backport of omp's identity card:
shipped generic, specialized in place. Every skill or agent that reads, writes, or promotes
document-style knowledge MUST obey this card — `docs-learn`, the `doc-inspector` agent
(read-only judgment reuse), `docs-pilot`'s wiki-capture step, `docs-standardize` (which
already induces a style-spec from N documents), and the `wiki/` accumulation behavior.

> **Identity in one line.** omd ships as a *generic* document harness (same logic for everyone)
> and becomes *specialized* purely through accumulated knowledge about this user/org's
> presentation style and working habits. Specialization is data, not code.

The path contract is `references/output-layout.md`. The induced style rules become a **durable**
style-spec at `.omd/wiki/convention/lab-style-spec.md` (a `<style-key>` scope uses a sibling
`.omd/wiki/convention/<key>-style-spec.md`) — the work-area, per-project, gitignored location the
`wiki/README.md` contract defines, where `docs-standardize`'s otherwise session-volatile spec is
persisted. The heavy channel promotes into *that* file (never the plugin repo). This card governs
the *dynamics*.

> **Provenance.** Backported from omp's `references/learning-protocol.md` (the omp heavy
> channel) on 2026-05-31, adapted to the document domain. Where omp promotes *file-moving
> rules* into `rules.json`, omd promotes *org-style defaults* into the style-spec. The two
> safety properties — human gate, deterministic grep recall — are carried over verbatim. The
> content-preservation invariant (§6.F) is omd's analogue of oms's citation-safety: omd never
> distorts a source document's facts/numbers/claims, and never promotes *content* — only form.

---

## 1. The two channels (asymmetric on purpose)

omd learns through **two channels with deliberately different friction**. A promoted default
changes what future document work *assumes by default*, so it pays a human gate; patterns and
decisions are cheap memory, so they accumulate freely.

```
                          OBSERVATION (something omd noticed about your document style)
                                              │
                ┌─────────────────────────────┴──────────────────────────────┐
                │                                                             │
        is it a candidate DEFAULT                              is it a PATTERN / DECISION
        (could auto-apply to future doc work)?                 (a note worth recalling later)?
                │                                                             │
        ── HEAVY CHANNEL (gated) ──                              ── LIGHT CHANNEL (no gate) ──
                │                                                             │
   learned.md  ──>  docs-learn  ──>  doc-inspector             wiki/<cat>/*.md  (auto-append)
   (observation     (promotion       (read-only judgment)               │
    accrues)         skill)               │                      next session: deterministic
                │                          ▼                      grep recall (no model search)
                │                  HUMAN APPROVAL GATE                     │
                │                          │                               ▼
                │                          ▼                      injected as context,
                └────────────────> style-spec  (specificity bump)  never auto-applied as default
```

### Heavy channel — DEFAULTS (`learned.md` → `docs-learn` → human gate → style-spec)

A **default** is anything a downstream omd stage would *assume without being told*: a caption
style ("12pt black"), a required slide ("contribution slide always present"), a title tone
("D-2 level"), a layout convention, a margin/font rule. `docs-standardize` already induces a
style-spec from N documents; the heavy channel **promotes a recurring observation into a
*learned, enforced* default in that spec**, raising specificity. Because a promoted default
silently shapes every future document for that org/type, it travels the gated path:

1. Observations accrue in `.omd/learned.md` (any read-only stage may append; see §2).
2. `docs-learn` reuses `doc-inspector` (read-only) to judge which observations are ripe (§3)
   and to draft the style-spec edit + the specificity recompute (§4).
3. **A human approves the promotion.** The single most important gate in omd.
4. On approval, the default is written into the style-spec, `specificity` is recomputed, the
   observation's id is recorded as provenance (`learned_refs`), and the paired human narrative
   is regenerated in the same pass so the spec never drifts from its provenance.

`doc-inspector` **judges only** — it never writes the style-spec itself in the learn flow; the
human gate plus `docs-learn`'s write step perform the write. (judgment ≠ approval ≠
enforcement — the three-way separation that forbids self-approval.)

### Light channel — PATTERNS / DECISIONS (`wiki/*.md` auto-append, grep recall, no gate)

A note about how this user works that is useful to *remember* but not enforceable: "reviews
the closing slide first", "prefers diagram-heavy", "this framing landed well". Auto-appends to
`.omd/wiki/<category>/*.md`, no gate, recalled by **deterministic grep** (§5). Context, never an
enforced default. Promotion (wiki insight → candidate default) only via `learned.md`.

### ⭐ Light-channel categories (4: the `pattern/` category is the oms/omd addition)

| category | holds | heavy-promotion candidate? |
|:---|:---|:---|
| `convention/` | how the output looks (caption style, layout, reject reasons) | **yes** — source of heavy candidates |
| `pattern/` | how the user works (`work-profile.md`, `working-style.md`, `preferences.md`) | **no** — disposition is not enforceable; light only |
| `decision/` | decisions made + rationale, what worked well | no |
| `reference/` | pointers to external material | no |

### Channel routing rule

| The observation… | Channel | Why |
|:---|:---|:---|
| could be auto-applied by a future stage (caption style, required slide, title tone) | **Heavy** (`learned.md`) | silently shapes future docs → needs the gate |
| is a fact, rationale, disposition, or decision worth remembering but not enforcing | **Light** (`wiki/`) | cheap memory → no gate |
| is ambiguous | **default to Light**, escalate later | safer to remember-without-enforcing |

### Capturing USER feedback (the most important, most-missed trigger)

The richest observations come from the **user correcting how omd works on their documents**:
"captions are always 12pt black", "defense decks always need a contribution slide", "titles
stay D-2". These encode intent, not a scan.

The failure this fixes: the model hears the correction, fixes the one instance, and **does not
write it down** — so it recurs. That is repeated apology, not learning.

**Trigger is durable and unconditional.** Whenever the user corrects/constrains/states a
preference about how omd handles *their documents* — in ANY turn:

1. **Route it.** Enforceable default → **Heavy**: append `OBS-NNNN` to `learned.md` with
   `source_stage: feedback`, `user_stated: true`. Working habit/disposition → **Light**:
   `wiki/pattern/*.md` or `wiki/decision/*.md`. Ambiguous → Light.
2. **⭐ user_stated bypasses the confidence gate, NOT the human gate (resolves review #1).** A
   `user_stated: true` candidate goes to the **human gate at `evidence_count: 1`** — it skips
   the §3.1 three-repetition bar (the user stated it directly, so one statement IS the intent),
   but it **still passes the human gate** (which scope? contradicts an existing default?) and
   **auto-promotion stays forbidden** (§6.B). Only path that skips repetition.
3. **Mark provenance.** `source_stage: feedback`, `user_overridden: false`; a contradicting
   feedback marks the existing default's candidate `user_overridden: true` (durable "no").
4. **Do it without being asked.** Document knowledge goes to *this harness's* `.omd/`, never to
   a distributed/user-scope config.

### 1.4 Two wiki levels — local (this document project) vs global (parent `.omd/`)

The light channel `wiki/` exists at **two levels**, both `.omd/`-relative (no absolute path,
no env var, no XDG — preserves "never to a distributed/user-scope config" above):

- **Local** = `<cwd>/.omd/wiki/` — knowledge specific to *this document project* (its defect
  patterns, its decisions). Stays with the project.
- **Global** = the nearest **ancestor `.omd/wiki/`** found by ascent (cwd → parent, first
  `.omd/` excluding self; git's `.git`-lookup pattern) — assets this *user/org* reuses across
  **every** document. Discovered, not configured: when the user runs from a documents-parent
  folder (e.g. their workspace), that folder's `.omd/` is the global level.

**What may rise to global** (the only things that leak upward — this is how the anti-pattern is
honored, not violated): reusable **form** assets only —

| category | global-eligible | why |
|:---|:---:|:---|
| `pattern/` (disposition: phrasing·layout·working-style·preferences) | ✅ light-only, never enforced | identity, doesn't change per document |
| `convention/` (org/lab style-spec, per-type form rules; scope `global \| <type-key>`) | ✅ via human gate (§6.B) | reused across documents |
| `decision/` (reusable decisions: "defense decks always lead with the contribution slide") | ✅ | meta-decisions across documents |
| this project's defect quirks / framing | ❌ stays local | project-specific, not reusable |
| **document content (text · claims · numbers · sources)** | ❌ **permanently forbidden** | content-preservation — §6.F invariant, never promoted to global (omd analogue of oms's citation-safety) |

The global level is *the parent folder's `.omd/`* (still work-root-relative), **not** a
distributed config — and only reusable form assets cross up. Project-specific knowledge stays
local and document content is forbidden. `wiki_query` merges both levels
(`references/wiki/README.md`), tagging `[wiki:local]`/`[wiki:global]`; the call site never changes.

⚠️ **Cross-project confidentiality gate (omd-specific — oms has no analogue).** The global level is
*shared by multiple document projects*, and any one of them may hold confidential material (a
client deck, an internal report). So a global-eligible note must carry only the
**abstracted form rule** ("captions are 12pt black"), never a **project-identifiable** detail
(client name, internal codename, a confidential path). "The ACME deck uses red captions" stays
**local** — promoting it would leak it into an unrelated project's session via ascent. Form
abstracts up; identifiers stay local. (`docs-pilot` only *hints* at promotion at terminal; the
actual local→global copy + identifier scrub is performed by `docs-learn` §4b through the human
gate — see `skills/docs-learn/SKILL.md` and §6.F.) The global-only `history/` category that oms
carries (for its `init`) is **not present** in omd — no `init` stage, no document-dedup need, so
it would be a dead category here.

---

## 2. The `learned.md` observation format (heavy-channel staging)

`.omd/learned.md` is an append-only ledger of candidate defaults awaiting promotion. Stages
append; only `docs-learn` (via the human gate) consumes/retires entries.

```
## OBS-<NNNN>  <one-line summary>
- id: OBS-<NNNN>
- channel: default
- status: candidate | promoted | rejected | superseded
- scope: global | <org-or-type-key>    # ⭐ global = universal habit; <key> = per-org/type (defense-deck, report)
- pattern: <precise, testable statement>
- candidate_default:                    # the exact style-spec edit this would become, if promoted
    target: style.caption | style.required_slides | style.title_tone | style.layout | global.<field>
    value: <concrete default>
    origin: learned
- evidence_count: <integer ≥ 1>         # how many distinct documents/sessions support it
- evidence:
    - <doc-slug or session event>
- counter_examples: <integer>           # documents that VIOLATE the pattern (> 0 blocks promotion)
- first_seen: <ISO date>
- last_seen: <ISO date>
- user_overridden: false
- user_stated: false                    # ⭐ true → evidence 1 is enough (§1.feedback.2)
- source_stage: inspect | verify | build | standardize | feedback
```

Worked example (per-type, observed):

```
## OBS-0005  Defense decks always use 12pt black captions
- id: OBS-0005
- channel: default
- status: candidate
- scope: defense-deck
- pattern: Every defense deck this user made ended with 12pt black captions (not 14pt grey).
- candidate_default:
    target: style.caption
    value: { size: 12pt, color: black }
    origin: learned
- evidence_count: 3
- evidence:
    - defense-2026-grasping (inspector flagged grey captions, user changed to 12pt black)
    - defense-2026-nav (same)
    - defense-2025-manip (same)
- counter_examples: 0
- first_seen: 2026-02-01
- last_seen: 2026-05-27
- user_overridden: false
- user_stated: false
- source_stage: inspect
```

Ledger rules (same as omp §2 / oms): append-only (re-observation bumps `evidence_count`),
concrete evidence (real doc-slugs/events — no guesses, §6.E), honest counter-examples, status
is a lifecycle not a delete.

---

## 3. Promotion criteria (the test `doc-inspector` applies)

`docs-learn` runs `doc-inspector` (read-only) against each `status: candidate`. Promotable to
the human gate **only if ALL hold** (AND, not a score):

1. **Repetition.** `evidence_count ≥ 3` across **distinct** documents/sessions (resolves
   review #2 — same bar omp §3.1 uses, "convention vs coincidence", not a magic number).
   **Exception:** `user_stated: true` skips this bar (§1.feedback.2) → gate at evidence 1.
2. **No counter-examples.** `counter_examples == 0` (from `wiki/convention/` scan — omd's
   equivalent of omp's wiki_lint contradiction check). A single violation blocks promotion.
3. **Not user-overridden.** `user_overridden == false`. The user's "no" is durable.
4. **Stability over time.** spans more than a single burst where feasible (soft; flagged at
   the gate as "burst evidence").
5. **Non-contradiction.** must not contradict a same-scope default in the style-spec unless
   framed as a replacement. Silent contradictions never auto-resolved.

`doc-inspector` outputs per ripe candidate: the style-spec edit, the specificity delta, the
provenance id, the scope, a one-line rationale. **Then stops at the gate.** Nothing reaches the
style-spec without explicit human approval. Failing candidates stay `candidate` (keep
accruing) — only the human or a counter-example sets `rejected`.

---

## 4. Specificity — what the `0..1` number means and how it's computed

`specificity` answers: **"how much of this org/type's style-spec is owned by *this user's*
learned habits, versus the generic template it started from?"** Tracked **per scope**.

- **0** — just deployed; every default is the generic template default.
- **1** — fully specialized; every active default was induced from real documents or promoted
  from a learned observation.

### Computation (per scope)

| origin | how it got there | weight |
|:---|:---|:---|
| `preset` | generic template default | 0.0 |
| `inductive` | induced by `docs-standardize` from real documents | 1.0 |
| `learned` | promoted from a `learned.md` observation through the gate | 1.0 |

```
specificity(scope) = (defaults with origin in {inductive, learned})
                     ──────────────────────────────────────────────
                     (total active defaults in that scope)
```

Each scope (`global`, `defense-deck`, `report`, …) has its own specificity — defense-deck
habits ≠ report habits.

### Monotonicity + the deletion rule (resolves review #3)

`specificity` MUST be **monotonic under promotion** (raise or hold, never silently lower).
Because the denominator can change when a default is **removed**, deletion is an explicit
recompute event: removing a default recomputes specificity in the **same pass**, records the
removal's provenance, and surfaces the new value at the gate. A specificity that changed with
no recorded cause is a §6.C violation.

---

## 5. The obsidian / second-brain analogy (wiki = grep-recalled notes)

Same as omp §5 / oms §5: `wiki/<category>/*.md` = a note, `[[backlinks]]` = plain-text
cross-refs, **grep = recall** (deterministic, CJK bi-gram, reproducible, no embedding drift).

### ⭐ confidence on wiki notes (OMC backport — H6)

Notes carry `confidence: high | med | low`; re-observation climbs `low → med → high`, merge
**keeps the higher**. A `convention/` note reaching **`confidence: high`** signals its `OBS`
likely hit `evidence_count ≥ 3` — worth a `docs-learn` look. Qualitative (3 levels + sighting
count) — **no numeric weighted sum, no threshold magic**. Append-only (dated `## <ISO> —`
sections; never overwrite a wiki note).

---

## 6. Anti-patterns (forbidden — these break the trust model)

### A. No embedding / semantic search for recall
Deterministic grep only (CJK bi-gram). No vector search/embeddings. Embedding recall can
surface a note that doesn't literally support a claim — omd recalls *exactly and only* what was
written.

### B. No auto-promotion without the human gate
A `learned.md` observation MUST NOT become a style-spec default without explicit human approval
— no `evidence_count`/`confidence` so high it bypasses the gate. `doc-inspector` judges; the
human disposes.

### C. No silent default changes
Every style-spec change MUST be (1) traceable to its origin (`learned_refs`/`origin: inductive`),
(2) reflected in the paired human narrative in the **same pass**, (3) accompanied by a
recomputed `specificity`. No provenance / moved specificity with no cause = violation
(`docs-verify` flags it, H10).

### D. (Corollary) No enforcement from the light channel
A `wiki/` note MUST NOT be treated as an enforceable default. Escalate to `learned.md` + gate.

### E. (Corollary) No fabricated evidence
`evidence[]` MUST cite real, enumerable doc-slugs/events. No inventing documents to reach `≥3`.

### F. ⚠️ No content promotion / distortion (omd-specific, absolute)
omd learns **form, never content**. A `candidate_default.target` naming a document's *content*
(specific text, a claim, a number, a source) is **rejected** — only form/style/layout targets
are allowed. And learning never licenses distorting a source document's facts/numbers/claims
(the content-preservation guardrail omd's translate/convert stages already enforce). 

Text-genre boundary examples (D7 — the form/content line is blurrier than in office decks, so
name it): learnable FORM — README section-order preference, voice, badge style, changelog
grouping convention, nav-structure pattern. Forbidden CONTENT — project facts, API names,
version numbers, link targets.

Form
specializes; content is preserved verbatim. This is omd's load-bearing invariant — the
analogue of oms's citation-safety.

This invariant extends to the **two-level wiki** (§1.4): document content is **permanently
forbidden from rising to the global level**, and a global-eligible note must be the abstracted
form rule, never a project-identifiable detail (client name, codename, confidential path) — the
**cross-project confidentiality gate**, since the global level is shared by multiple document
projects that may include confidential material. Identifiers stay local; only abstracted form
crosses up.

---

## 7. End-to-end trace (how one learned default happens)

1. **operation** — the user makes 3 defense decks. Each time `docs-inspect` flags "grey
   captions" and the user changes them to 12pt black. `docs-pilot`'s wiki-capture appends to
   `.omd/wiki/convention/defense-deck-*.md`; by the 3rd the note's `confidence` reaches `high`.
   The disposition "reviews closing slide first" lands in `wiki/pattern/working-style.md` (light).
2. **observation** — staged in `learned.md` as `OBS-0005`, `scope: defense-deck`,
   `candidate_default: {target: style.caption, value: {size:12pt, color:black}}`, evidence 3,
   counter-examples 0.
3. **learn** — `docs-learn` runs. `doc-inspector` checks §3: all pass. Drafts the style-spec
   edit + specificity bump + provenance, **stops at the gate**.
4. **gate** — the human approves. `docs-learn` writes the default into the defense-deck
   style-spec (caption: 12pt black, origin: learned), sets `OBS-0005.status: promoted`, records
   provenance, recomputes `specificity(defense-deck)` upward, regenerates the narrative.
5. **enforce** — from now on `docs-build` lays captions as 12pt black by default for defense
   decks, without the user asking. Specialized to *this user's defense-deck habit* — every step
   on disk, inspectable, reversible.

---

## See also

- `references/output-layout.md` — where `.omd/` files live.
- `references/wiki/README.md` — light-channel categories + append/confidence discipline.
- `.omd/wiki/convention/lab-style-spec.md` — the durable style-spec `docs-standardize` persists and
  the heavy-channel promotion target (per-project, in the work area, never the plugin repo).
- omp `references/learning-protocol.md` — the upstream (same two-channel design; omp promotes
  file-rules, omd promotes style-defaults). oms's card is the sibling (promotes venue-defaults).
