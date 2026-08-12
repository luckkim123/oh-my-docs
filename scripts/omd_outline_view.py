"""Parse an approved docs-plan `## Outline` section (GATE1 output) into structured
data, so it can be persisted and rendered as a reviewable sheet instead of being
lost after the human approves it in chat.

`parse_outline` is pure and never raises: malformed input becomes an absence
(``None``, ``""``, ``[]``) for a later stage (`flags()`) to report, not an
exception here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


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


_ARC_RE = re.compile(r"\*\*Arc/Frame\*\*:\s*(.+)")
_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_SEP_ROW_RE = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_SECTIONS_RE = re.compile(r"Required sections all placed:\s*(.+)")
_DENSITY_RE = re.compile(r"Density limits respected:\s*(.+)")


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
    """Split a markdown table row into cells, or None if not a row / a separator row."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    if _SEP_ROW_RE.match(stripped):
        return None
    # Strip leading/trailing pipe, tolerate a row with or without the trailing one.
    inner = stripped[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [cell.strip() for cell in inner.split("|")]


def _parse_number(cell: str) -> int | None:
    """`#` cell -> int, or None for anything non-integer (dotted, blank, text)."""
    if re.fullmatch(r"\d+", cell):
        return int(cell)
    return None


def _parse_units(section: str) -> list[Unit]:
    units: list[Unit] = []
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
        padded = (cells + [""] * 5)[:5]
        number = _parse_number(padded[0])
        units.append(Unit(number=number, name=padded[1], purpose=padded[2],
                           message=padded[3], asset=padded[4]))
    return units


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
    units = _parse_units(outline_section) if outline_section is not None else []

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
                    questions=questions)


@dataclass
class Flag:
    code: str
    detail: str


# "none" is a legitimate Required-asset value (nothing needed); it is not a
# stand-in for "missing". Open Questions uses a separate vocabulary for "no
# question here" — mixing the two is the trap this module exists to avoid.
_ASSET_NONE_VALUES = {"none"}
_NO_QUESTION_VALUES = {"none", "n/a", ""}


def flags(outline: Outline) -> list[Flag]:
    """Structural absence checks over a parsed Outline (spec Sec 3.4, 9 codes).

    Every check asks only "is a character present or not" — never whether a
    cell's content is good. Pure, never raises, order is first-occurrence
    while walking the document top to bottom.
    """
    out: list[Flag] = []

    arc = (outline.arc or "").strip()
    arc_why = (outline.arc_why or "").strip()
    if not arc or not arc_why:
        out.append(Flag("missing-arc", "Arc/Frame or its Why is missing or empty"))

    units = outline.units or []
    if not units:
        out.append(Flag("no-units", "the Outline section has no unit rows"))
    else:
        for unit in units:
            for column, value in (("name", unit.name), ("purpose", unit.purpose),
                                   ("message", unit.message)):
                value = (value or "").strip()
                if not value or value.casefold() == "tbd":
                    out.append(Flag("missing-field", f"unit {unit.number}: {column} is missing"))
            asset = (unit.asset or "").strip()
            if asset.casefold() not in _ASSET_NONE_VALUES and (
                    not asset or asset.casefold() == "tbd"):
                out.append(Flag("missing-field", f"unit {unit.number}: asset is missing"))

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
                                 f"'{name}' appears at units {seen[name]} and {position}"))
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


def render_html(outline: Outline, flagged: list[str]) -> str:
    """Task 3 — not yet implemented."""
    raise NotImplementedError("render_html() is Task 3")


def main() -> int:
    """Task 3 — not yet implemented."""
    raise NotImplementedError("main() is Task 3")


if __name__ == "__main__":
    import sys
    sys.exit(main())
