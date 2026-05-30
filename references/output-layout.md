# Output Layout — directory & naming convention (OMD)

> **What this is**: A data file, not a skill. The OMD agents and stage skills (`docs-build`,
> `doc-builder`, `doc-verifier`, `docs-pilot`) read this card for the single, fixed answer to
> "where does each file go." Same input → always the same path. It is the SSOT for output paths;
> the format cards (`references/formats/<format>.md`) point here for layout.

**Design principle**: the layout is a *deterministic, fixed structure* — it does not vary by task
or format. The user sees exactly one finished copy in `outputs/`; everything the user does not need
to look at directly (version copies, PNG renders, generated images, temp files) lives in the `.omd/`
work area. The work area is cleaned when the pipeline reaches a terminal state or on request.

All paths are **relative to the work root** (the caller's working directory or an explicitly named
project root) — never hardcoded to any one machine or absolute path.

---

## 0. The two areas (invariant)

| Area | What goes in | Who reads it | Cleaned? |
|:---|:---|:---|:---:|
| `outputs/<slug>/` | **The one copy the user sees** (`current.<ext>`) + optional verify evidence | the user | ❌ never touched automatically (user asset) |
| `.omd/<slug>/` | Everything the user rarely needs directly — version copies, PNG renders, gen-image, temp | Claude (analysis) | ✅ confirmed-then-cleaned at terminal |

**Core**: `outputs/` is the "display shelf — this is the result right now," exactly one copy.
`.omd/` is the "workbench." Even versions count as work-product and live on the workbench. This
structurally prevents the common failure where the output folder bloats with snapshots and
intermediates mixed in with the final deliverable.

---

## 1. slug generation (deterministic)

Each job's folder name = **`{YYYY-MM-DD}_{kebab-title}`**.

### 1.1 Algorithm (same input → always the same slug)

```
slug = "{ISO_DATE}_{KEBAB}"

ISO_DATE = job start date YYYY-MM-DD (current date; never an arbitrary past date)
KEBAB    = normalize(title):
  1) English title input (if the title is non-ASCII → ask the user once for an ASCII slug;
     do NOT auto-romanize)
  2) lowercase
  3) spaces / underscores → '-'
  4) drop everything matching [^a-z0-9-]
  5) collapse runs of '-' → single '-', trim leading/trailing '-'
  6) length > 40 → cut at a word boundary at 40
```

Examples:
- "Defense Final" + 2026-05-30 → `2026-05-30_defense-final`
- "Q3 Board Review" → `2026-05-30_q3-board-review`

### 1.2 Non-ASCII titles (explicit)

Non-ASCII titles (CJK, Cyrillic, …) are **never auto-romanized** — romanization differs by tool and
locale, which breaks "same input → same slug," and it invites filesystem encoding issues (e.g.
NFC/NFD on case-insensitive filesystems). At the intake stage, ask the user once for an ASCII slug.
The confirmed slug is then fixed for the life of the job (never re-asked).

### 1.3 slug collisions (deterministic)

- Same day + same title → same slug → treated as **continuing the same job** (append, not
  overwrite). For a genuinely separate job, the user gives a different title.
- Different day + same title → the date prefix separates them naturally.
- The slug is fixed once at job start and is immutable for the job's lifetime.

---

## 2. Fixed directory structure (invariant — does not vary)

```
outputs/<slug>/
  current.<ext>                       # the one copy the user sees (.pptx/.docx/.hwpx). The PASS copy.
  verify-evidence.md                  # (optional) verification evidence table — for the user

.omd/<slug>/                          # work area — everything the user rarely needs directly
  versions/
    v{NN}_{YYYY-MM-DD}_{summary}.<ext>   # version copies (§3 rules)
  renders/
    current/                          # latest PNG renders of current.<ext> (inspect/verify, ≥150 dpi)
      slide-{NNN}.png
    v{NN}/                            # (optional) renders kept for a specific version
      slide-{NNN}.png
  gen-image/
    {YYYY-MM-DD}_{purpose}.png        # generated diagrams/backgrounds (§4 rules)
  tmp/
    *                                 # soffice pdf / pdftoppm intermediates — disposable anytime
  build-notes.md                      # (optional) builder notes — for Claude's analysis

.omd/wiki/                            # project-wide accrual — NOT per-job (sibling of <slug>/, carries across sessions)
  convention/  decision/  reference/  # auto-appended defect patterns / style specs / decisions (see references/wiki/README.md)
```

### 2.1 Invariance rules

- The four subdirectories (`versions/ renders/ gen-image/ tmp/`) are **always this name, this
  place**. They do not change by job type or format.
- The structure is identical even when empty (a job that uses no gen-image either leaves an empty
  `gen-image/` or simply omits it — but never invents a different name for it).
- A new kind of intermediate maps into one of the four (no inventing a new top-level folder). Only a
  genuinely new category that maps to none of them is added by amending this convention.

---

## 3. Version filename rule (deterministic)

Version copies under `.omd/<slug>/versions/`:

**`v{NN}_{YYYY-MM-DD}_{summary}.<ext>`**

```
v{NN}        = zero-padded 2-digit version number. v01, v02, … v10, v11. (so v1 and v10 sort right)
{YYYY-MM-DD} = the snapshot's date
{summary}    = short kebab-case summary (same KEBAB rule as §1.1, length ≤ 30)
```

Examples:
- `v01_2026-05-30_initial.pptx`
- `v02_2026-05-31_section-reorder.pptx`

### 3.1 When to snapshot

- **Only before a large edit** (section add/remove, structural change, many slides/pages affected).
  Not for a one-line tweak, a typo, or a single caption — this keeps the version count bounded.
- A snapshot **copies** `current.<ext>` to `versions/v{NN}_{date}_{summary}.ext` (copy, not move —
  `current` stays and work continues on it).
- `NN` = max existing version number + 1; if empty, `v01`.
- `current` is always the single `outputs/<slug>/current.<ext>` — the latest working copy.
  `versions/` holds past snapshots.

### 3.2 Why zero-pad

`ls` sorts lexically: without padding, `v1, v10, v2` is wrong. With `v01, v02, … v10`, chronological
order = version number order = sort order, always.

---

## 4. gen-image / render PNG naming

### 4.1 gen-image (`gen-image/`)

`{YYYY-MM-DD}_{purpose}.png` — purpose is kebab. e.g. `2026-05-30_pipeline-diagram.png`,
`2026-05-30_seafloor-bg.png`.

- **Separate from any image tool's own default path**: an external image-generation tool may have
  its own default output location, but in a *document workflow* the caller explicitly directs output
  to `.omd/<slug>/gen-image/`.
- Do not conflate a general image store with *work-area intermediate images*.

### 4.2 render PNGs (`renders/`)

- inspect/verify renders `current.<ext>` to PNG → `renders/current/slide-{NNN}.png`. NNN
  zero-padded 3 digits.
- Re-rendering the same job overwrites `renders/current/` (only the latest matters). Keep a specific
  version's render only when needed, under `renders/v{NN}/`.

---

## 5. Terminal cleanup (T18 — pilot end-of-pipeline)

### 5.1 Trigger

- (a) the pilot pipeline reaches terminal (verify PASS + user's final confirmation), **or**
- (b) the user explicitly says "clean up" / "we're done."

### 5.2 Scope (intermediates + old versions together)

| Target | Clean | Note |
|:---|:---:|:---|
| `.omd/<slug>/renders/` | ✅ all | Claude analysis, regenerable |
| `.omd/<slug>/gen-image/` | ✅ all | except images the user asks to keep |
| `.omd/<slug>/tmp/` | ✅ all | build/convert intermediates |
| `.omd/<slug>/versions/` | ✅ **all but the latest 1 + user-designated milestones** | keep the near-final copy, prune the middle |
| `outputs/<slug>/current.<ext>` | ❌ never | user asset — excluded from tally and deletion, mentioned only |

### 5.3 Safe procedure

1. **Tally** the cleanup targets under `.omd/<slug>/`: size and count
   (e.g. "renders 12, gen-image 3, tmp, 5 old versions = 0.4 GB").
2. **Ask the user [clean / keep]** — never auto-delete. Default conservative (keep).
3. On "clean" → **delete via a recoverable path** (never permanent `rm`). Environment-adaptive:
   - macOS: use the `trash` CLI if present, else move to `~/.Trash`
   - Linux desktop: `gio trash` / `trash-cli`
   - Windows: send to the Recycle Bin via PowerShell
     (`powershell -c "(New-Object -ComObject Shell.Application).Namespace(0).ParseName('<abs-path>').InvokeVerb('delete')"`),
     or the `recycle-bin` / `trash` module if installed; never `Remove-Item` permanently
     (documented; unverified on Windows)
   - no-trash environment (CI / container / minimal): confirm "permanent delete" with the user
     explicitly before any `rm`
4. Verify what remains (latest 1 version + milestones still present).

### 5.4 Absolute rules

- `outputs/` is never touched automatically by any cleanup.
- On "keep," leave everything — no forcing.
- Deletion always goes through a recoverable path (trash). Permanent deletion is forbidden.

---

## 6. Implementation checklist (consumers of this card)

- [ ] `docs-build` / `docs-pilot` / `doc-builder` express the working copy as `outputs/<slug>/current.<ext>`
- [ ] version snapshots and PNG renders go under `.omd/<slug>/{versions,renders}/`, not `outputs/`
- [ ] `doc-verifier` checks `.omd/<slug>/versions/` count against the prune threshold
- [ ] `.gitignore` excludes `.omd/` and `outputs/*` (keep `outputs/.gitkeep`)
- [ ] slug rule (§1.1) applied at intake (non-ASCII → ask once for an ASCII slug)
- [ ] terminal cleanup (§5) goes through AskUserQuestion + trash + excludes `outputs/current.<ext>`
