"""Parse an approved docs-plan `## Outline` section (GATE1 output) into structured
data, so it can be persisted and rendered as a reviewable sheet instead of being
lost after the human approves it in chat.

`parse_outline` is pure and never raises: malformed input becomes an absence
(``None``, ``""``, ``[]``) for a later stage (`flags()`) to report, not an
exception here.
"""
from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Unit:
    number: int | None
    name: str
    purpose: str
    message: str
    asset: str


@dataclass
class Outline:
    arc: str
    arc_why: str
    units: list[Unit] = field(default_factory=list)
    coverage_sections: str | None = None
    coverage_density: str | None = None
    has_coverage_check: bool = False
    questions: list[str] = field(default_factory=list)
    # 1-based reading-order positions of Outline rows that did not split into
    # exactly 5 cells (see _parse_units) — a malformed-row flag, not silently
    # padded/truncated into a wrong-shaped Unit.
    malformed_rows: list[int] = field(default_factory=list)


# [ \t]*, not \s* — \s matches a newline, so \s* before the capture group
# would swallow a blank "**Arc/Frame**:" line's trailing newlines and let
# (.+) bleed into the next line's unrelated text (fix round 2). Bounding the
# gap to the same line makes an empty Arc/Frame line fail to match here, so
# _ARC_RE.search() falls through to "no match" and flags() reports
# missing-arc correctly instead of reading the next paragraph as the arc.
_ARC_RE = re.compile(r"\*\*Arc/Frame\*\*:[ \t]*(.+)")
_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_SEP_ROW_RE = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_SECTIONS_RE = re.compile(r"Required sections all placed:[ \t]*(.*)")
_DENSITY_RE = re.compile(r"Density limits respected:[ \t]*(.*)")
# Table-cell split point: a "|" not preceded by a backslash, so an escaped
# "\|" inside a cell (e.g. "Before \| After") stays in the cell instead of
# shifting every following column one to the right.
_ROW_SPLIT_RE = re.compile(r"(?<!\\)\|")

# A cell that carries no real content: known placeholder tokens, or a
# bracketed template stub like "[Insert title]" / "[named arc]" left over
# from the planner's own <Output_Format> example (agents/doc-planner.md).
# Still pure character-presence — no reading for sense.
_PLACEHOLDER_VALUES = {"", "tbd", "…", "...", "n/a", "-"}
_BRACKET_PLACEHOLDER_RE = re.compile(r"^\[.+\]$")


def _is_placeholder(value: str | None) -> bool:
    v = (value or "").strip()
    if v.casefold() in _PLACEHOLDER_VALUES:
        return True
    return bool(_BRACKET_PLACEHOLDER_RE.match(v))


def _section_body(text: str, heading: str) -> str | None:
    """Return the body text of a `## <heading>` section, or None if absent.

    Matches on the heading prefix (not full-line equality) so a heading with a
    trailing parenthetical, e.g. "## Open Questions (if any block the structure)",
    still matches a lookup for "Open Questions".
    """
    heading_re = re.compile(r"^##\s+" + re.escape(heading) + r"(\s|\(|$)")
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if heading_re.match(line):
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for i in range(start, len(lines)):
        if _SECTION_RE.match(lines[i]):
            end = i
            break
    return "\n".join(lines[start:end])


def _parse_row(line: str) -> list[str] | None:
    """Split a markdown table row into cells, or None if not a row / a separator row.

    Splits on unescaped "|" only, so a literal pipe inside a cell must be
    written "\\|" to survive (fix round: an unescaped mid-cell pipe used to
    shift every following column one to the right, silently).
    """
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    if _SEP_ROW_RE.match(stripped):
        return None
    # Strip leading/trailing pipe, tolerate a row with or without the trailing one.
    inner = stripped[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [cell.strip().replace("\\|", "|") for cell in _ROW_SPLIT_RE.split(inner)]


def _parse_number(cell: str) -> int | None:
    """`#` cell -> int, or None for anything non-integer (dotted, blank, text)."""
    if re.fullmatch(r"\d+", cell):
        return int(cell)
    return None


def _parse_units(section: str) -> tuple[list[Unit], list[int]]:
    units: list[Unit] = []
    malformed: list[int] = []
    for line in section.splitlines():
        cells = _parse_row(line)
        if cells is None:
            continue
        # Header row ("# | Name | Purpose | ..."): skip by looking for a non-numeric,
        # non-empty first cell that isn't parseable as a unit number and reads like
        # a header label rather than data. Since a real data row's first cell is
        # always meant to be a number, the safest signal is a literal "#" or "Number".
        if cells and cells[0].strip().lower() in ("#", "number", "no", "no."):
            continue
        if len(cells) != 5:
            malformed.append(len(units) + 1)
        padded = (cells + [""] * 5)[:5]
        number = _parse_number(padded[0])
        units.append(Unit(number=number, name=padded[1], purpose=padded[2],
                           message=padded[3], asset=padded[4]))
    return units, malformed


def parse_outline(text: str) -> Outline:
    arc_match = _ARC_RE.search(text)
    arc = ""
    arc_why = ""
    if arc_match:
        arc_line = arc_match.group(1)
        if "**Why**:" in arc_line:
            arc_part, why_part = arc_line.split("**Why**:", 1)
            arc = arc_part.rstrip(" —-").strip()
            arc_why = why_part.strip()
        else:
            arc = arc_line.strip()

    outline_section = _section_body(text, "Outline")
    units, malformed_rows = (_parse_units(outline_section) if outline_section is not None
                              else ([], []))

    coverage_section = _section_body(text, "Coverage Check")
    has_coverage_check = coverage_section is not None
    coverage_sections = None
    coverage_density = None
    if has_coverage_check:
        sections_match = _SECTIONS_RE.search(coverage_section)
        density_match = _DENSITY_RE.search(coverage_section)
        coverage_sections = sections_match.group(1).strip() if sections_match else ""
        coverage_density = density_match.group(1).strip() if density_match else ""

    questions_section = _section_body(text, "Open Questions")
    questions: list[str] = []
    if questions_section is not None:
        for line in questions_section.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                questions.append(stripped[2:].strip())

    return Outline(arc=arc, arc_why=arc_why, units=units,
                    coverage_sections=coverage_sections,
                    coverage_density=coverage_density,
                    has_coverage_check=has_coverage_check,
                    questions=questions,
                    malformed_rows=malformed_rows)


@dataclass
class Flag:
    code: str
    detail: str
    # 1-based position(s) in outline.units this flag concerns, in reading
    # order — () for the 7 codes that aren't about a specific unit. Lets the
    # renderer mark panels without re-parsing `detail` text.
    unit_pos: tuple[int, ...] = ()


# "none" is a legitimate Required-asset value (nothing needed); it is not a
# stand-in for "missing". Open Questions uses a separate vocabulary for "no
# question here" — mixing the two is the trap this module exists to avoid.
_ASSET_NONE_VALUES = {"none"}
_NO_QUESTION_VALUES = {"none", "n/a", ""}


def flags(outline: Outline) -> list[Flag]:
    """Structural absence checks over a parsed Outline (spec Sec 3.4's 9 codes,
    plus `malformed-row` — see its definition below for why it was added).

    Every check asks only "is a character present or not" — never whether a
    cell's content is good. Pure, never raises, order is first-occurrence
    while walking the document top to bottom.
    """
    out: list[Flag] = []

    arc = outline.arc
    arc_why = outline.arc_why
    if _is_placeholder(arc) or _is_placeholder(arc_why):
        out.append(Flag("missing-arc", "Arc/Frame or its Why is missing or empty"))

    units = outline.units or []
    if not units:
        out.append(Flag("no-units", "the Outline section has no unit rows"))
    else:
        for position, unit in enumerate(units, start=1):
            for column, value in (("name", unit.name), ("purpose", unit.purpose),
                                   ("message", unit.message)):
                if _is_placeholder(value):
                    out.append(Flag("missing-field", f"unit {unit.number}: {column} is missing",
                                     unit_pos=(position,)))
            asset = (unit.asset or "").strip()
            if asset.casefold() not in _ASSET_NONE_VALUES and _is_placeholder(asset):
                out.append(Flag("missing-field", f"unit {unit.number}: asset is missing",
                                 unit_pos=(position,)))

        # Not one of the spec's original 9 codes (deferred to implementation
        # per team-lead review): a row that split into other than 5 cells is
        # a structural defect distinct from any existing code — no-units
        # doesn't apply (units exist), missing-field doesn't apply (a
        # shifted-column row can have every resulting cell non-empty and
        # still be wrong), and there's no reading-for-sense involved, only
        # a cell count. Kept out of the exact-code-set tests' expectations
        # unless a fixture actually trips it.
        for position in outline.malformed_rows:
            out.append(Flag("malformed-row",
                             f"unit at position {position} does not have exactly 5 columns",
                             unit_pos=(position,)))

        expected = list(range(1, len(units) + 1))
        actual = [u.number for u in units]
        if actual != expected:
            out.append(Flag("number-gap", f"expected 1..{len(units)}, saw {actual}"))

        seen: dict[str, int] = {}
        for position, unit in enumerate(units, start=1):
            name = (unit.name or "").strip()
            if not name:
                continue
            if name in seen:
                out.append(Flag("duplicate-unit",
                                 f"'{name}' appears at units {seen[name]} and {position}",
                                 unit_pos=(seen[name], position)))
            else:
                seen[name] = position

    if not outline.has_coverage_check:
        out.append(Flag("no-coverage-check", "the Coverage Check section is missing"))
    else:
        sections = outline.coverage_sections or ""
        if sections.strip().casefold() != "yes":
            out.append(Flag("coverage-unresolved", sections))
        density = outline.coverage_density or ""
        if density.strip().casefold() != "yes":
            out.append(Flag("density-unresolved", density))

    for question in (outline.questions or []):
        if (question or "").strip().casefold() not in _NO_QUESTION_VALUES:
            out.append(Flag("open-questions", question))

    return out


def _flagged_positions(flagged: list[Flag]) -> set[int]:
    """1-based positions (reading order) any flag concerns — never a unit's
    own `#` value, which can differ from its position when number-gap or
    duplicate-unit has also fired.
    """
    refs: set[int] = set()
    for f in flagged:
        refs.update(f.unit_pos)
    return refs


def _render_panel(unit: Unit, position: int, refs: set[int]) -> str:
    number_display = str(unit.number) if unit.number is not None else "—"
    is_flagged = position in refs
    css_class = "panel panel--flagged" if is_flagged else "panel"
    badge = '<span class="panel-badge">FLAGGED</span>' if is_flagged else ""
    return f"""      <article class="{css_class}">
        <div class="panel-head"><span class="panel-number">{html.escape(number_display)}</span>{badge}</div>
        <h3>{html.escape(unit.name)}</h3>
        <p class="panel-purpose">{html.escape(unit.purpose)}</p>
        <p class="panel-message">{html.escape(unit.message)}</p>
        <span class="panel-asset">{html.escape(unit.asset)}</span>
      </article>"""


def render_html(outline: Outline, flagged: list[Flag]) -> str:
    """One self-contained HTML page: the arc as frame, units as a panel strip
    in reading order, and every flag's detail — a gate1 review sheet, not a
    verdict. No score, no grade, no "looks good" — GAPS=0 means nothing is
    mechanically absent, not that the structure is approved.
    """
    refs = _flagged_positions(flagged)
    panels = "\n".join(_render_panel(u, i, refs) for i, u in enumerate(outline.units, start=1))
    panel_strip = (panels if outline.units
                   else '      <p class="empty-note">No unit rows to display.</p>')

    if flagged:
        gap_items = "\n".join(
            f'        <li><span class="gap-code">{html.escape(f.code)}</span> '
            f'{html.escape(f.detail)}</li>'
            for f in flagged)
        gaps_html = f'      <ul class="gaps-list">\n{gap_items}\n      </ul>'
    else:
        gaps_html = '      <p class="empty-note">No structural gaps detected.</p>'

    arc = html.escape(outline.arc) if outline.arc else "—"
    arc_why = html.escape(outline.arc_why) if outline.arc_why else "—"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>GATE1 Outline Review</title>
<style>
:root {{
  --bg: #ffffff;
  --fg: #1a1a1a;
  --muted: #5c5c5c;
  --panel-bg: #f7f7f8;
  --panel-border: #d9d9dc;
  --flag-bg: #fdf1f1;
  --flag-border: #b3261e;
  --accent: #2c5aa0;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #17171a;
    --fg: #eaeaea;
    --muted: #a3a3a8;
    --panel-bg: #232327;
    --panel-border: #3a3a40;
    --flag-bg: #3a2222;
    --flag-border: #e57373;
    --accent: #85a8db;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #17171a;
  --fg: #eaeaea;
  --muted: #a3a3a8;
  --panel-bg: #232327;
  --panel-border: #3a3a40;
  --flag-bg: #3a2222;
  --flag-border: #e57373;
  --accent: #85a8db;
}}
* {{ box-sizing: border-box; }}
body {{
  background: var(--bg);
  color: var(--fg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 0;
  padding: 2rem;
  line-height: 1.4;
}}
h1 {{ font-size: 1.3rem; margin: 0 0 0.5rem; }}
h2 {{ font-size: 1rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
.frame {{ margin: 0 0 2rem; color: var(--muted); }}
.frame strong {{ color: var(--fg); }}
.gaps-list {{ list-style: none; margin: 0; padding: 0; }}
.gaps-list li {{
  padding: 0.4rem 0.6rem;
  margin-bottom: 0.3rem;
  background: var(--flag-bg);
  border-left: 3px solid var(--flag-border);
}}
.gap-code {{ font-family: monospace; font-weight: bold; margin-right: 0.5rem; }}
.empty-note {{ color: var(--muted); }}
.panel-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}}
.panel {{
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 6px;
  padding: 0.8rem;
}}
.panel--flagged {{ border-color: var(--flag-border); background: var(--flag-bg); }}
.panel-head {{ display: flex; align-items: center; justify-content: space-between; }}
.panel-number {{
  display: inline-block;
  font-family: monospace;
  font-weight: bold;
  color: var(--accent);
}}
.panel-badge {{
  font-size: 0.7rem;
  font-weight: bold;
  letter-spacing: 0.04em;
  border: 1px solid var(--flag-border);
  color: var(--flag-border);
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
}}
.panel h3 {{ margin: 0.4rem 0 0.3rem; font-size: 1rem; }}
.panel-purpose {{ color: var(--muted); margin: 0 0 0.3rem; }}
.panel-message {{ margin: 0 0 0.5rem; }}
.panel-asset {{
  display: inline-block;
  font-size: 0.75rem;
  background: var(--panel-border);
  border-radius: 3px;
  padding: 0.1rem 0.4rem;
}}
footer {{ margin-top: 2rem; color: var(--muted); font-size: 0.8rem; }}
</style>
</head>
<body>
  <header>
    <h1>GATE1 Outline Review</h1>
    <p class="frame"><strong>Frame:</strong> {arc} &nbsp;·&nbsp; <strong>Why:</strong> {arc_why}</p>
  </header>
  <section class="gaps">
    <h2>Gaps ({len(flagged)})</h2>
{gaps_html}
  </section>
  <section class="panels">
    <h2>Units</h2>
    <div class="panel-grid">
{panel_strip}
    </div>
  </section>
  <footer>
    <p>`GAPS=0` means nothing mechanical is missing — it is <strong>not</strong> a judgment that the structure is good.</p>
  </footer>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a GATE1 outline review sheet.")
    parser.add_argument("input", help="path to the approved outline markdown file")
    parser.add_argument("-o", "--output", help="output HTML path (default: gate1.html beside input)")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.is_file():
        parser.error(f"no such file: {args.input}")

    output_path = Path(args.output) if args.output else input_path.parent / "gate1.html"

    outline = parse_outline(input_path.read_text(encoding="utf-8"))
    flagged = flags(outline)

    # Write unconditionally, before deciding the exit code — a defective
    # outline is exactly when the user most needs the sheet.
    output_path.write_text(render_html(outline, flagged), encoding="utf-8")

    for f in flagged:
        print(f"{f.code}: {f.detail}")
    print(f"GAPS={len(flagged)}")

    return 1 if flagged else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
