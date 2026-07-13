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
