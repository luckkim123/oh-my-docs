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

def test_docs_plan_names_the_renderer_and_outline_path():
    body = _read("skills/docs-plan/SKILL.md")
    assert "omd_outline_view.py" in body
    assert ".omd/<slug>/outline.md" in body


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
