"""scripts/omd_outline_view.py — Task 1: parse_outline.

COMPLETE is the pinned healthy fixture from docs/superpowers/plans/2026-08-12-
gate1-outline-view.md ("The fixture, pinned once"). Copied verbatim; do not
"clean up" its em-dash or spacing — Tasks 2-3 build defect tests as COMPLETE
plus exactly one mutation, and this file is the shared baseline for that diff.
"""
import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "omd_outline_view.py"

_spec = importlib.util.spec_from_file_location("omd_outline_view", SCRIPT)
ov = importlib.util.module_from_spec(_spec)
sys.modules["omd_outline_view"] = ov   # required before exec: @dataclass under PEP 563
                                       # resolves annotations via sys.modules[cls.__module__]
_spec.loader.exec_module(ov)

parse_outline = ov.parse_outline

COMPLETE = """## Narrative Arc
**Arc/Frame**: defense (question - contribution - method - experiment - conclusion) — **Why**: a committee judges novelty first, then rigor.

## Outline
| # | Slide/Section | Purpose | Key message | Required asset |
|---|---------------|---------|-------------|----------------|
| 1 | Title | frame the talk | who, what, and when | none |
| 2 | Research question | establish the gap | localization fails under drift | figure |
| 3 | Contribution | state what is new | we add an adaptive filter | none |
| 4 | Method | show it is sound | the filter works by re-weighting | figure |
| 5 | Experiment | show it holds | it beats the baseline on the metric | table |

## Coverage Check
- Required sections all placed: yes
- Density limits respected: yes

## Open Questions (if any block the structure)
- none
"""


def test_complete_parses_five_units_in_order():
    outline = parse_outline(COMPLETE)
    assert len(outline.units) == 5
    assert outline.units[0].name == "Title"
    assert outline.units[4].asset == "table"


def test_arc_and_why_are_split_without_cross_contamination():
    outline = parse_outline(COMPLETE)
    assert outline.arc == "defense (question - contribution - method - experiment - conclusion)"
    assert outline.arc_why == "a committee judges novelty first, then rigor."
    assert "**Why**" not in outline.arc
    assert "Arc/Frame" not in outline.arc_why


def test_separator_row_not_parsed_as_unit():
    outline = parse_outline(COMPLETE)
    # 5 data rows only — the |---|---| header separator must not become a 6th unit.
    assert len(outline.units) == 5
    assert all(u.name != "" for u in outline.units)


def test_trailing_pipe_optional_and_parses_identically():
    with_pipe = "| 1 | Title | frame the talk | who, what, and when | none |"
    without_pipe = "| 1 | Title | frame the talk | who, what, and when | none"
    text_with = f"## Outline\n{with_pipe}\n"
    text_without = f"## Outline\n{without_pipe}\n"
    units_with = parse_outline(text_with).units
    units_without = parse_outline(text_without).units
    assert units_with == units_without
    assert units_with[0].asset == "none"


def test_missing_outline_section_yields_empty_units_no_raise():
    text = "## Narrative Arc\n**Arc/Frame**: defense — **Why**: because.\n"
    outline = parse_outline(text)
    assert outline.units == []


def test_missing_arc_line_yields_empty_string_no_raise():
    text = "## Outline\n| # | Slide/Section | Purpose | Key message | Required asset |\n|---|---|---|---|---|\n| 1 | Title | x | y | none |\n"
    outline = parse_outline(text)
    assert outline.arc == ""


def test_non_numeric_number_cell_yields_none_no_raise():
    text = "## Outline\n| abc | Title | frame the talk | who, what, and when | none |\n"
    outline = parse_outline(text)
    assert len(outline.units) == 1
    assert outline.units[0].number is None


def test_coverage_check_absent_has_flag_false_fields_none():
    text = "## Outline\n| 1 | Title | x | y | none |\n"
    outline = parse_outline(text)
    assert outline.has_coverage_check is False
    assert outline.coverage_sections is None
    assert outline.coverage_density is None
    # None, distinct from "" — a present-but-empty field must not collapse to absence.
    assert outline.coverage_sections != ""


def test_multi_digit_and_dotted_numbers_survive():
    rows = "\n".join(f"| {n} | Unit {n} | p | m | a |" for n in range(1, 13))
    text = f"## Outline\n{rows}\n"
    outline = parse_outline(text)
    assert [u.number for u in outline.units] == list(range(1, 13))

    dotted_text = "## Outline\n| 4.5 | Sub-unit | p | m | a |\n"
    dotted = parse_outline(dotted_text)
    assert len(dotted.units) == 1
    assert dotted.units[0].number is None  # not silently truncated to 4
