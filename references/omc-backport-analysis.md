# OMC Backport Analysis — oh-my-docs (omd)

omd's intake ambiguity gate, consensus layer, inspector critic techniques, and runtime accumulation (wiki/notepad/
verifier tokens) are the verified patterns of **oh-my-claudecode (OMC)** ported into the document/slide
domain. When OMC is updated, we need a persistent baseline for judging *what changed and whether omd needs
to be updated*. OMC has no CHANGELOG (only GitHub commits/releases exist) and no per-file versions, so
this document itself holds the "diff baseline".

> **This document lives in a distributed plugin's references/, so it is independent of any personal environment.** OMC paths are written *only* as
> the *public plugin's internal structure* (relative expressions). No specific machine's absolute paths, work notes, or user's organizational system are embedded.

---

## §1. OMC 4.14.4 Structure Snapshot — backport source components

The OMC plugin has a **dual structure**: `skill-bodies/<name>/SKILL.md` holds the full logic, and
`skills/<name>/SKILL.md` is a *compact reference shim* that keeps the startup context light
(it loads the body from `skill-bodies/`). The backport source is always the `skill-bodies/` side.

| Source (OMC 4.14.4 internal path) | What was brought over |
|:---|:---|
| `skill-bodies/deep-interview/SKILL.md` | Round 0 topology · per-dimension ambiguity judgment · challenge agents (contrarian/simplifier/ontologist) · soft limits · 3-point injection → the ambiguity-reinforcing skeleton of **docs-intake** |
| `skill-bodies/plan/SKILL.md`, `skill-bodies/ralplan/SKILL.md` | RALPLAN-DR consensus (Principles/Drivers/Options≥2/steelman/tradeoff/ADR) · sequential-enforcement (no-parallel) prompt discipline → **doc-planner** + **docs-plan --consensus** |
| `skill-bodies/autopilot/SKILL.md` | brief→completion stage orchestration + gate skeleton → **docs-pilot** |
| `skill-bodies/ralph/SKILL.md` | defect=PRD · fix/verify loop until the passes:true gate · no scope reduction → **docs-revise** (already present, unchanged in this backport) |
| `agents/analyst.md` | pre-diagnosis · requirements-analysis philosophy → intent crystallization in docs-intake |
| `agents/architect.md` | steelman/antithesis/tradeoff → **absorbed into doc-planner** (no separate agent created) |
| `agents/planner.md` | narrative arc · outline → doc-planner |
| `agents/critic.md` | pre-commitment · assumption (VERIFIED/REASONABLE/FRAGILE) · pre-mortem · self-audit → the **4 techniques of doc-inspector** |
| OMC MCP tool servers (`wiki_*`/`notepad_*`/`shared_memory_*`/`state_*`) | accumulation · compaction-survival · handoff *philosophy*. ⚠️ omd defaults to **.md degrade** and MCP is an optional accelerator — no new Node MCP is added |

---

## §2. Analysis baseline version + diff baseline

- **Analysis baseline snapshot = OMC 4.14.4.** This is the OMC version this document saw when reading the backport source
  (at that time the plugin's `package.json`, `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json`
  all three carried `"version": "4.14.4"`). **This is an *analysis-time snapshot*, not a runtime pin** —
  the omc marketplace declaration in `~/.claude/settings.json` (`repo: Yeachan-Heo/oh-my-claudecode`) has
  no version or commit-SHA, so **OMC always auto-follows the marketplace latest**. Nowhere in oms/omd is there
  a pin tying OMC to a specific version. Therefore no separate work is needed for an OMC upgrade, and
  the diff baseline below is only for re-examining *whether the backport adopt/exclude decisions still hold*.
- **diff baseline**: OMC has no CHANGELOG (only GitHub commits/releases). On the next OMC update,
  look directly at the diffs of the §1 source files above (`skill-bodies/{deep-interview,plan,ralplan,autopilot,ralph}/SKILL.md`,
  `agents/{analyst,architect,planner,critic}.md`) and judge whether omd needs updating.
- Judgment rule: if an OMC update changes an ***adopted* area in §3** → consider a corresponding backport update.
  If it newly touches an ***excluded* area in §3** → re-examine whether the exclusion decision still holds.

---

## §3. Adopt/Exclude mapping (internal backport work ID = Tn)

> Tn is this repo's internal backport work identifier (mnemonic). Each row self-describes *what changed*,
> so it reads without an external plan document. Isomorphic with oms (papers), differing only in domain.

### Adopt

| Tn | OMC pattern | omd application (actual change) |
|:---|:---|:---|
| T1 | the stage boundaries of deep-interview/ralplan | intake↔plan↔consensus boundary convention. doc-architect·docs-plan-consensus **not newly created** (absorbed into doc-planner·docs-plan modes) |
| T3 | critic 4 techniques + severity | in `agents/doc-inspector.md`, **introduce the severity axis first** (1st severity / 2nd rank / confidence is the severity axis), then insert pre-commitment·assumption (V/R/F)·pre-mortem·self-audit *inside* the PPTEval 3 axes. **rank is omd-specific** (ordering many slide findings) — the isomorphism with oms goes only as far as "severity axis + 4 techniques" |
| T6 | ralplan RALPLAN-DR + architect | in `agents/doc-planner.md`, RALPLAN-DR + steelman + ADR. The three `'One arc only'` clauses are *not deleted* but mode-aware edited (--direct=preserve a single arc, --consensus=Options≥2→converge to a final single arc in plan.md). `skills/docs-plan/SKILL.md` --consensus mode |
| T7 | shared_memory handoff | inter-consensus-stage transfer = `<slug>/consensus/*.md` files as the **default**, MCP as an optional mirror (degrades to .md when absent) |
| T9 | deep-interview gate | in `skills/docs-intake/SKILL.md`, keep gate 0 (5-field Socratic) + Round 0 topology + 4-dimension **qualitative** judgment (Audience/Message/Evidence-density/Constraint, zero quantification) + 3 challenge types + ambiguity-resolution round loop |
| T8b | autopilot wiring | in `skills/docs-pilot/SKILL.md` `<Steps>`, insert the docs-plan --consensus branch (Deliberate trigger = defense/examination/external official presentation) — the engine actually fires on the autopilot path (preventing dead code) |
| T10 | wiki accumulation | data lives in the project workspace `.omd/wiki/*.md` (gitignored, OMC `.omc/wiki/` pattern) + deterministic grep as the **default**, `wiki_query(category)` is an abstract function (future MCP swap point). Only the contract doc is the plugin `references/wiki/README.md`. The style spec docs-standardize induces is compounded as the "lab standard" |
| T11 | notepad compaction-survival | on docs-pilot entry, in the `## Priority Context` section of `.omd/notepad.md`, no in-place edits of the original + gate logging (.md default) |
| T12 | verifier request-id | in `agents/doc-verifier.md`, a snapshot correlation token (current.<ext> mtime·CRC + defect ID) — blocks stale-PASS reuse in multi-round revise |
| T14 | (omd's own routing) | add a `revise` token to the `hooks/route_emit.py` STAGE catalog (docs-revise exists but was missing — fixed) + a Deliberate→`--consensus` rationale hint. New regression test `tests/test_route_emit.py` (omd's first tests/) |
| T15 | state path | workspace = fixed `.omd/<slug>/` (removing the unverified `.omd/specs`·`sessions/{sid}` segments). The 30s state-MCP trap is *just a future-proofing memo* |
| T16 | (contract history) | new `CHANGELOG.md` — keep commit-SHA versioning but explicitly record hook contract changes (tone unified with oms [0.1.1]) |

### Exclude (with rationale)

| OMC pattern | Exclusion rationale |
|:---|:---|
| **newly creating** doc-architect / docs-plan-consensus and the like | duplicates doc-planner·docs-plan modes → absorbed as an extension |
| **structure-regression clause (T13)** | not applied to omd — docs-revise already defends sufficiently via acceptance (full PNG read-through + "the FAIL defect of the immediately preceding round does not reproduce"). Applied asymmetrically only to oms (scholar-revise) |
| **actual state MCP calls** | excessive for the single·sequential philosophy. notepad (.md) survives compaction better. The 30s trap is documentation only |
| persistent-mode **Stop-hook enforcement** | freeze risk, the revise loop is sufficient. On hold |
| **ambiguity quantification** (weighted sum·threshold·stability_ratio) | qualitative gate adopted — weak rationale for magic numbers |
| **multi-perspective / realist / adversarial escalation** | duplicates pre-mortem·self-audit, and conflicts with the inspector's formative "stop when read & ranked" (blurs the formative↔verify boundary) |
| code-only runtimes 15+ (comment-checker·code-simplifier·ast/lsp·python_repl·ultragoal·loop_authority etc.) | domain-irrelevant |
| **embedding search** | deterministic matching only, so wiki accumulation does not drag in hallucinations (permanently prohibited, now and in the future) |

---

## §4. Reverse review — omp → omd backport (2026-05-31, adopted 0)

This document is originally OMC → omd direction, but it also examines, by the same yardstick, whether
**what sibling omp added in 0.2.0** (omp's `references/omc-backport-analysis.md`
T17~T25 — the result of omp pushing the OMC backport deeper than omd) is worth *reverse*-backporting into omd.
(The verdict is persistently recorded so the next session does not repeat the same analysis.)

**omp 0.2.0's 5 new types → omd adoption = 0.** In adversarial verification (propose↔refute, 2026-05-31, against omd's actual source), all 5 candidates were rejected:

| omp 0.2.0 candidate | omd verdict | Main rationale |
|:---|:---|:---|
| `content_conventions[]` rule type | REJECT | domain mismatch + duplication — omd is a *generation pipeline* that produces a new `.pptx/.docx/.hwpx` (binary OOXML/HWPX) on every run. `scope: body\|frontmatter` loses its referent (slides have no frontmatter, and 'body' is the set of shapes/runs across N slides). present/absent text conventions are already covered by the PPTEval Content axis (placeholder-absent·density) + plan/verify. |
| content audit axis (`check_content_rule`) | REJECT | omd has no rules.json regex rule engine (grep returns 0). The transferable core (severity error→gate FAIL) is already equivalently held by docs-verify's loud integrity 5/5 gate. Its verification paradigm is the PPTEval 3-axis rubric (qualitative) + full PNG read-through, orthogonal to a regex engine. |
| dead-link (`find_dead_links`, `[[backlink]]`) | REJECT | domain asymmetry — omd outputs are binary office files, not a `.md` graph. The `[[backlink]]` integrity of `.omd/wiki/` is only a *nice-to-have* health-hint, not a required feature (per the don't-overreach guideline). |
| `.omp/CONVENTIONS.md` | REJECT | the prose mirror of content_conventions[] — without the underlying machine rules in omd, it would be an orphan narrative. omd's "convention document" role is already performed by the **style spec** that `docs-standardize` induces from N documents. |
| specificity content term | REJECT | **intended absence** — omd, in learning-protocol §5 H6, *explicitly prohibits* "no numeric weighted sum, no threshold magic", and the omc-backport-analysis §3 exclusion table already excludes "ambiguity quantification (weighted sum)". C5 is exactly the category omd intentionally rejected. Moreover, omd specificity (learning-protocol §4) is a simple coverage ratio, not a multi-term decomposition axis of structure/naming/content, so there is no coordinate to slot it into. |

**Conclusion**: omp 0.2.0 is intrinsic to the omp domain (a management loop that repeatedly re-inspects a living `.omp/`
with rules.json regexes), so there is nothing to flow into omd in any form — code, prose, or health-hint. Isomorphic
with the 2026-05-31 omx wiki comparison analysis (5 REJECT of 6 candidates). The T20~T25 where omp backported *OMC* more deeply
are also unsuitable for omd (irrelevant to the generation domain), so there is no separate adoption.

---

**Analysis snapshot**: OMC 4.14.4 (not a runtime pin — auto-follows marketplace latest, §2) · **isomorphic sibling**: oh-my-scholar `references/omc-backport-analysis.md` (paper domain) · **reverse review**: omp 0.2.0 → omd adoption 0 (§4)
