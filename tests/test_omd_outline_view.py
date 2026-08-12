"""scripts/omd_outline_view.py — Task 1: parse_outline.

COMPLETE is the pinned healthy fixture from docs/superpowers/plans/2026-08-12-
gate1-outline-view.md ("The fixture, pinned once"). Copied verbatim; do not
"clean up" its em-dash or spacing — Tasks 2-3 build defect tests as COMPLETE
plus exactly one mutation, and this file is the shared baseline for that diff.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "omd_outline_view.py"

_spec = importlib.util.spec_from_file_location("omd_outline_view", SCRIPT)
ov = importlib.util.module_from_spec(_spec)
sys.modules["omd_outline_view"] = ov   # required before exec: @dataclass under PEP 563
                                       # resolves annotations via sys.modules[cls.__module__]
_spec.loader.exec_module(ov)

parse_outline = ov.parse_outline
flags = ov.flags
render_html = ov.render_html
main = ov.main


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


# Fix round 1 (task-2 review) — _SECTIONS_RE / _DENSITY_RE used \s* before the
# capture group, which swallows the newline and bleeds into the next line's
# text when the planner's line has nothing after the colon. Regression tests
# for the two states that must stay distinct: present-but-empty ("") vs
# absent (None).

def test_coverage_line_present_but_empty_does_not_bleed_into_next_line():
    text = ("## Coverage Check\n"
            "- Required sections all placed:\n"
            "- Density limits respected: yes\n")
    outline = parse_outline(text)
    assert outline.coverage_sections == ""
    assert outline.coverage_density == "yes"


def test_both_coverage_lines_present_but_empty_stay_independently_empty():
    text = ("## Coverage Check\n"
            "- Required sections all placed:\n"
            "- Density limits respected:\n")
    outline = parse_outline(text)
    assert outline.coverage_sections == ""
    assert outline.coverage_density == ""


def test_coverage_section_absent_still_yields_none_after_regex_fix():
    text = "## Outline\n| 1 | Title | x | y | none |\n"
    outline = parse_outline(text)
    assert outline.has_coverage_check is False
    assert outline.coverage_sections is None
    assert outline.coverage_density is None


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


# Task 3 — render_html() and main(). DEFECTIVE is COMPLETE plus exactly one
# mutation (unit 3's purpose cell emptied): one flag, five units, all names
# intact — enough to check both "every unit name appears" and "every flag
# detail appears" in the same fixture.

DEFECTIVE = COMPLETE.replace(
    "| 3 | Contribution | state what is new | we add an adaptive filter | none |",
    "| 3 | Contribution |  | we add an adaptive filter | none |")


def test_render_html_contains_every_unit_name_and_flag_detail():
    outline = parse_outline(DEFECTIVE)
    flagged = flags(outline)
    assert flagged  # sanity: this fixture does trip a flag
    out = render_html(outline, flagged)
    for unit in outline.units:
        assert unit.name in out
    for f in flagged:
        assert f.detail in out


def test_render_html_escapes_script_tag_in_a_cell():
    text = COMPLETE.replace(
        "| 3 | Contribution | state what is new | we add an adaptive filter | none |",
        "| 3 | Contribution | state what is new | <script>alert(1)</script> | none |")
    outline = parse_outline(text)
    out = render_html(outline, flags(outline))
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out


def test_render_html_has_all_three_theme_selectors():
    outline = parse_outline(COMPLETE)
    out = render_html(outline, flags(outline))
    assert "@media (prefers-color-scheme: dark)" in out
    assert ':root:not([data-theme="light"])' in out
    assert ':root[data-theme="dark"]' in out


def test_render_html_no_units_flag_detail_survives_empty_panel_strip():
    # The bug the sibling repo shipped: no-units left the panel strip empty
    # AND dropped the flag's own detail, so the page explained nothing.
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
    outline = parse_outline(text)
    assert outline.units == []
    flagged = flags(outline)
    out = render_html(outline, flagged)
    assert "the Outline section has no unit rows" in out


def test_main_on_healthy_outline_returns_0_writes_file_and_prints_gaps_0(tmp_path, capsys):
    input_path = tmp_path / "outline.md"
    input_path.write_text(COMPLETE, encoding="utf-8")
    output_path = tmp_path / "gate1.html"
    code = main([str(input_path), "-o", str(output_path)])
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert code == 0
    assert out_lines == ["GAPS=0"]
    assert output_path.is_file()


def test_main_on_defective_outline_returns_1_writes_file_and_prints_one_line_per_gap(
        tmp_path, capsys):
    input_path = tmp_path / "outline.md"
    input_path.write_text(DEFECTIVE, encoding="utf-8")
    output_path = tmp_path / "gate1.html"
    code = main([str(input_path), "-o", str(output_path)])
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert code == 1
    assert len(out_lines) == 2  # one gap line + GAPS=<n>
    assert out_lines[-1] == "GAPS=1"
    assert output_path.is_file()


def test_main_writes_file_even_when_every_flag_fires(tmp_path, capsys):
    # Near-empty input trips missing-arc, no-units, no-coverage-check.
    input_path = tmp_path / "outline.md"
    input_path.write_text("## Narrative Arc\n", encoding="utf-8")
    output_path = tmp_path / "gate1.html"
    code = main([str(input_path), "-o", str(output_path)])
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert code == 1
    assert output_path.is_file()
    assert output_path.read_text(encoding="utf-8")
    assert out_lines[-1].startswith("GAPS=")
    assert int(out_lines[-1].removeprefix("GAPS=")) == len(out_lines) - 1


def test_main_default_output_path_is_gate1_html_beside_input(tmp_path):
    input_path = tmp_path / "outline.md"
    input_path.write_text(COMPLETE, encoding="utf-8")
    main([str(input_path)])
    assert (tmp_path / "gate1.html").is_file()


def test_main_missing_input_file_goes_through_parser_error(tmp_path, capsys):
    missing = tmp_path / "nope.md"
    with pytest.raises(SystemExit):
        main([str(missing)])


# Fix round 1 (task-3 review) — duplicate-unit's positions and a unit's own
# `#` value were conflated into one string-keyed ref set, so an unrelated
# unit whose `#` happened to equal a duplicate's position got wrongly
# flagged. Root fix: Flag carries unit_pos (reading-order positions), never
# matched against unit.number.

def _panel_blocks_for(out: str, name: str) -> list[str]:
    """Each panel's HTML, from its <article ...> to the next one, for a
    given unit name — a duplicate name yields more than one block.
    """
    parts = out.split("<article")[1:]
    return [f"<article{p}" for p in parts if f"<h3>{name}</h3>" in p]


def test_unrelated_unit_not_flagged_when_its_number_collides_with_a_duplicate_position():
    text = ("## Narrative Arc\n**Arc/Frame**: x — **Why**: y.\n\n"
            "## Outline\n"
            "| 5 | Foo | p | m | none |\n"
            "| 9 | Foo | p | m | none |\n"
            "| 1 | Bar | p | m | none |\n")
    outline = parse_outline(text)
    flagged = flags(outline)
    assert {f.code for f in flagged} == {"number-gap", "duplicate-unit", "no-coverage-check"}
    out = render_html(outline, flagged)

    (bar_block,) = _panel_blocks_for(out, "Bar")
    assert "panel--flagged" not in bar_block  # Bar's "#" is 1, same digit as
                                               # the duplicate's positions — must not match

    foo_blocks = _panel_blocks_for(out, "Foo")
    assert len(foo_blocks) == 2
    assert all("panel--flagged" in b for b in foo_blocks)


def test_missing_field_flags_panel_by_position_not_by_number_value():
    # Position 1 has "#" = 9 (matches nothing); position 2 has a blank
    # purpose. Only position 2's panel may be flagged.
    text = ("## Narrative Arc\n**Arc/Frame**: x — **Why**: y.\n\n"
            "## Outline\n"
            "| 9 | Alpha | p | m | none |\n"
            "| 2 | Beta |  | m | none |\n")
    outline = parse_outline(text)
    flagged = flags(outline)
    assert {f.code for f in flagged} == {"missing-field", "number-gap", "no-coverage-check"}
    out = render_html(outline, flagged)

    (alpha_block,) = _panel_blocks_for(out, "Alpha")
    (beta_block,) = _panel_blocks_for(out, "Beta")
    assert "panel--flagged" not in alpha_block
    assert "panel--flagged" in beta_block
