# Theme Presets — fallback style data

> Data file, not a skill. 10 preset font/color themes for use when `docs-build` / `docs-standardize`
> hit the "no reference document → default tone preset" branch and need something concrete to fall
> back on, instead of an undefined default.
>
> Borrowed from awesome-claude-skills `theme-factory`, 2026-07-09. License: Apache-2.0
> (`LICENSE.txt` in this folder). Only the preset **data** (palettes, font pairings, showcase PDF) was
> ported — the custom-theme-generation logic was intentionally left out (see below).
>
> **Office formats only (F8).** These presets are font/color palettes for render-capable
> office documents. Text genres never fall back here — their no-reference fallback is
> defined by their format card (repo-docs: genre section presets; site: the
> mkdocs-material `palette:` schema).

## When this applies

`docs-standardize`'s `Do_Not_Use_When` and `docs-pilot`'s stage 2 both say: *"no reference documents
exist → skip (use the default tone preset)."* Today that "default tone preset" is undefined — there is
no concrete fallback style. This folder is that fallback:

- If the user supplied reference documents → `docs-standardize` induces the style spec from them.
  **Do not use this folder** in that case; the induced spec always wins over a generic preset.
- If no reference documents exist and the user has no house style → offer these 10 presets as a
  concrete starting point instead of guessing at colors/fonts. `docs-build` (or `doc-builder`) can read
  the chosen preset's `.md` file directly for hex codes + font pairing.

## Choosing a preset

1. Show `theme-showcase.pdf` (all 10 themes rendered together) as a visual picker — same gate pattern
   `theme-factory`'s own `SKILL.md` used ("show the showcase, ask which one, wait for confirmation").
   Do not modify the PDF; it is a preview asset only.
2. Ask which theme fits the content/audience (each preset file has a "Best Used For" line to guide
   the pick).
3. Read that theme's `.md` file for the hex palette + header/body font pairing and apply it in the
   build step (`docs-build`).

## The 10 presets

| Theme | Palette mood | Header / Body font | Best used for |
|:---|:---|:---|:---|
| [ocean-depths](ocean-depths.md) | Navy / teal / seafoam | DejaVu Sans Bold / DejaVu Sans | Corporate, financial, consulting |
| [sunset-boulevard](sunset-boulevard.md) | Burnt orange / coral / warm sand | DejaVu Serif Bold / DejaVu Sans | Creative pitches, marketing, lifestyle |
| [forest-canopy](forest-canopy.md) | Forest green / sage / olive | FreeSerif Bold / FreeSans | Environmental, sustainability, wellness |
| [modern-minimalist](modern-minimalist.md) | Charcoal / slate gray grayscale | DejaVu Sans Bold / DejaVu Sans | Tech, architecture, data visualization |
| [golden-hour](golden-hour.md) | Mustard / terracotta / warm beige | FreeSans Bold / FreeSans | Restaurant, hospitality, artisan |
| [arctic-frost](arctic-frost.md) | Ice blue / steel blue / silver | DejaVu Sans Bold / DejaVu Sans | Healthcare, tech, clean tech |
| [desert-rose](desert-rose.md) | Dusty rose / clay / sand | FreeSans Bold / FreeSans | Fashion, beauty, wedding, interior design |
| [tech-innovation](tech-innovation.md) | Electric blue / neon cyan / dark gray | DejaVu Sans Bold / DejaVu Sans | Tech startups, AI/ML, software launches |
| [botanical-garden](botanical-garden.md) | Fern green / marigold / terracotta | DejaVu Serif Bold / DejaVu Sans | Garden, food, farm-to-table, natural products |
| [midnight-galaxy](midnight-galaxy.md) | Deep purple / cosmic blue / lavender | FreeSans Bold / FreeSans | Entertainment, gaming, luxury, creative agencies |

## Explicitly out of scope

- **Custom theme generation** (theme-factory's "Create your Own Theme" section — inducing a new
  palette from a free-form description) was **not** ported. That overlaps with `docs-standardize`,
  which already inductively extracts a style spec from real reference documents — a stronger,
  evidence-based version of the same idea. Two theme-derivation paths would duplicate logic and
  invite drift.
- Fonts here are the fixed-installation fallback fonts (DejaVu/FreeSans/FreeSerif family) from the
  original toolkit, chosen for wide availability — swap for house fonts when a real style spec exists.
