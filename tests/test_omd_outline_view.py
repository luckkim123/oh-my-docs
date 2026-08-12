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
flags = ov.flags


def codes(text: str) -> set[str]:
    return {f.code for f in flags(parse_outline(text))}

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


# Task 2 — flags(). Each test is COMPLETE plus exactly one mutation, asserting
# exact set equality against spec sec 3.4's 9 codes.

def test_complete_trips_no_flags():
    assert codes(COMPLETE) == set()


def test_purpose_cell_emptied_is_missing_field():
    text = COMPLETE.replace(
        "| 3 | Contribution | state what is new | we add an adaptive filter | none |",
        "| 3 | Contribution |  | we add an adaptive filter | none |")
    assert codes(text) == {"missing-field"}


def test_purpose_cell_tbd_is_missing_field():
    text = COMPLETE.replace(
        "| 3 | Contribution | state what is new | we add an adaptive filter | none |",
        "| 3 | Contribution | TBD | we add an adaptive filter | none |")
    assert codes(text) == {"missing-field"}


def test_asset_none_is_legitimate_not_missing_field():
    # unit 1's asset is already "none" in COMPLETE — guards the vocabulary
    # mixup ("none" means no-question in Open Questions, but a legitimate
    # value here in Required asset).
    assert codes(COMPLETE) == set()


def test_outline_table_removed_is_no_units():
    text = COMPLETE.replace(
        """## Outline
| # | Slide/Section | Purpose | Key message | Required asset |
|---|---------------|---------|-------------|----------------|
| 1 | Title | frame the talk | who, what, and when | none |
| 2 | Research question | establish the gap | localization fails under drift | figure |
| 3 | Contribution | state what is new | we add an adaptive filter | none |
| 4 | Method | show it is sound | the filter works by re-weighting | figure |
| 5 | Experiment | show it holds | it beats the baseline on the metric | table |

""", "")
    assert codes(text) == {"no-units"}


def test_arc_line_removed_is_missing_arc():
    text = COMPLETE.replace(
        "**Arc/Frame**: defense (question - contribution - method - experiment - conclusion) "
        "— **Why**: a committee judges novelty first, then rigor.\n", "")
    assert codes(text) == {"missing-arc"}


def test_why_half_emptied_frame_kept_is_missing_arc():
    text = COMPLETE.replace(
        "— **Why**: a committee judges novelty first, then rigor.", "— **Why**: ")
    assert codes(text) == {"missing-arc"}


def test_unit_numbers_with_a_gap_is_number_gap():
    text = (COMPLETE
            .replace("| 3 | Contribution", "| 4 | Contribution")
            .replace("| 4 | Method", "| 5 | Method")
            .replace("| 5 | Experiment", "| 6 | Experiment"))
    assert codes(text) == {"number-gap"}


def test_unit_numbers_with_a_duplicate_number_is_number_gap():
    text = (COMPLETE
            .replace("| 3 | Contribution", "| 2 | Contribution")
            .replace("| 4 | Method", "| 3 | Method")
            .replace("| 5 | Experiment", "| 4 | Experiment"))
    assert codes(text) == {"number-gap"}


def test_renamed_unit_colliding_with_another_is_duplicate_unit():
    text = COMPLETE.replace("| 5 | Experiment |", "| 5 | Method |")
    assert codes(text) == {"duplicate-unit"}


def test_coverage_check_section_removed_is_no_coverage_check():
    text = COMPLETE.replace(
        """## Coverage Check
- Required sections all placed: yes
- Density limits respected: yes

""", "")
    assert codes(text) == {"no-coverage-check"}


def test_sections_line_not_yes_is_coverage_unresolved():
    text = COMPLETE.replace(
        "- Required sections all placed: yes",
        "- Required sections all placed: no — Related Work missing")
    assert codes(text) == {"coverage-unresolved"}


def test_density_line_not_yes_is_density_unresolved():
    text = COMPLETE.replace(
        "- Density limits respected: yes",
        "- Density limits respected: flag: slide 4 title 62 chars")
    assert codes(text) == {"density-unresolved"}


def test_real_open_question_is_open_questions():
    text = COMPLETE.replace("- none", "- which dataset ships?")
    assert codes(text) == {"open-questions"}


def test_open_questions_section_removed_is_clean():
    text = COMPLETE.replace(
        """## Open Questions (if any block the structure)
- none
""", "")
    assert codes(text) == set()


def test_open_questions_item_n_a_is_clean():
    text = COMPLETE.replace("- none", "- n/a")
    assert codes(text) == set()


def test_several_mutations_return_all_their_flags():
    text = COMPLETE.replace(
        "**Arc/Frame**: defense (question - contribution - method - experiment - conclusion) "
        "— **Why**: a committee judges novelty first, then rigor.\n", "")
    text = text.replace(
        "| 3 | Contribution | state what is new | we add an adaptive filter | none |",
        "| 3 | Contribution |  | we add an adaptive filter | none |")
    text = text.replace(
        "| 5 | Experiment | show it holds | it beats the baseline on the metric | table |",
        "| 6 | Experiment | show it holds | it beats the baseline on the metric | table |")
    text = text.replace(
        """## Coverage Check
- Required sections all placed: yes
- Density limits respected: yes

""", "")
    text = text.replace("- none", "- which dataset ships?")
    assert codes(text) == {"missing-arc", "missing-field", "number-gap",
                            "no-coverage-check", "open-questions"}


def test_flags_never_returns_a_code_outside_the_nine():
    known = {"missing-field", "no-units", "missing-arc", "number-gap",
             "duplicate-unit", "no-coverage-check", "coverage-unresolved",
             "density-unresolved", "open-questions"}
    garbage = ov.Outline(
        arc="", arc_why="",
        units=[ov.Unit(number=None, name="", purpose="", message="", asset="")],
        coverage_sections="no", coverage_density="no",
        has_coverage_check=True,
        questions=["what dataset?"],
    )
    result = {f.code for f in flags(garbage)}
    assert result <= known
    assert flags(garbage)  # ran without raising
