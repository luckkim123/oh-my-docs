"""Gate 1 outline-view wiring (Tasks 5-6): docs-plan saves/renders the approved
outline to `.omd/<slug>/outline.md` / `gate1.html`, and the five downstream
consumers all name that same path instead of an untethered "the approved
outline". Structural existence checks live in test_skill_contract.py /
test_skill_lint.py / test_agent_contract.py — this file only checks the
specific sentences this wiring requires.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent

GAPS_ZERO_SENTENCE = (
    "`GAPS=0` means nothing mechanical is missing — it is **not** a judgment "
    "that the structure is good, and must never be presented as one."
)


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


# --- Task 5: docs-plan / doc-planner -----------------------------------

ANCHORED_RENDER_COMMAND = "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/omd_outline_view.py"


def test_docs_plan_names_the_renderer_and_outline_path():
    body = _read("skills/docs-plan/SKILL.md")
    assert "omd_outline_view.py" in body
    assert ".omd/<slug>/outline.md" in body


def test_docs_plan_render_command_is_anchored_to_plugin_root():
    # Regression guard: "python3 scripts/..." resolves scripts/ relative to
    # the CALLER's cwd (the user's document project), not the omd plugin
    # install, and fails with [Errno 2] at runtime. Both --direct (step 4)
    # and --consensus (step 6c) must use the anchored form.
    body = _read("skills/docs-plan/SKILL.md")
    assert body.count(ANCHORED_RENDER_COMMAND) == 2
    assert "python3 scripts/omd_outline_view.py" not in body


def test_docs_plan_notes_nonzero_exit_means_gaps_not_failure():
    # A Bash-tool caller reads a non-zero exit as failure; main() returns 1
    # whenever any flag fired (spec Sec 3.3), which is the normal outcome on
    # a defective outline — exactly when the gap report matters most.
    body = _read("skills/docs-plan/SKILL.md")
    assert body.count("non-zero exit means") == 2


def test_docs_plan_carries_gaps_zero_sentence_verbatim():
    body = _read("skills/docs-plan/SKILL.md")
    assert GAPS_ZERO_SENTENCE in body


def test_doc_planner_stays_read_only():
    fm = _read("agents/doc-planner.md")
    assert "disallowedTools: Write" in fm


# --- Task 6: the five downstream consumers -----------------------------

DOWNSTREAM_FILES = [
    "agents/doc-builder.md",
    "agents/doc-verifier.md",
    "skills/docs-verify/SKILL.md",
    "skills/docs-build/SKILL.md",
    "skills/docs-revise/SKILL.md",
]


def test_downstream_files_name_the_outline_path():
    missing = [f for f in DOWNSTREAM_FILES if ".omd/<slug>/outline.md" not in _read(f)]
    assert not missing, f"missing outline path reference: {missing}"
