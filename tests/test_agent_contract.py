"""Agent contract guards (R1): frontmatter model policy (G4 precondition) and, from
Task 11, the Final_Response_Contract markers (AC-1a). stdlib frontmatter parse only.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
AGENTS_DIR = ROOT / "agents"

# Deliberate judgment lanes (inspector/verifier) run opus; production lanes run sonnet.
# doc-planner is sonnet by default — Deliberate consensus escalates at Task-call time
# (skills/docs-plan SKILL.md --consensus path), never via frontmatter.
EXPECTED_MODELS = {
    "doc-analyzer": "sonnet",
    "doc-builder": "sonnet",
    "doc-planner": "sonnet",
    "doc-inspector": "opus",
    "doc-verifier": "opus",
}


def _frontmatter(name: str) -> dict:
    lines = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", f"{name}: frontmatter must open the file"
    fm = {}
    for line in lines[1:]:
        if line == "---":
            return fm
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    raise AssertionError(f"{name}: unterminated frontmatter")


def test_agent_model_policy():
    for name, model in EXPECTED_MODELS.items():
        assert _frontmatter(name).get("model") == model, (
            f"{name}: frontmatter model must be {model} (spec §3.1 G4 / critique #2)"
        )


# Final_Response_Contract (AC-1a): the markers each agent's Output_Format promises.
# These are the strings downstream consumers (skills, humans) grep for — losing one
# in a doc rewrite is a silent contract break (exactly how H2 happened).
REQUIRED_MARKERS = {
    "doc-verifier": ["### Verdict", "**Status**: PASS | FAIL"],
    "doc-inspector": ["## Formative Review"],
    "doc-planner": ["## Narrative Arc", "## Outline", "## Coverage Check"],
    "doc-analyzer": ["## Source Inventory", "## Reference Design System"],
    "doc-builder": ["## Artifact", "## Build Notes"],
}

# Self-approval ban is load-bearing prose for the two review lanes only (spec §3.4 AC-1a).
SELF_APPROVAL_BANS = {
    "doc-verifier": "never self-approve",
    "doc-inspector": "never approve work",
}


def _body(name: str) -> str:
    return (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def test_final_response_contract_markers():
    for name, markers in REQUIRED_MARKERS.items():
        body = _body(name)
        for marker in markers:
            assert marker in body, f"{name}: required output marker {marker!r} missing"


def test_self_approval_ban_present():
    for name, phrase in SELF_APPROVAL_BANS.items():
        assert phrase in _body(name), f"{name}: self-approval ban phrase {phrase!r} missing"
