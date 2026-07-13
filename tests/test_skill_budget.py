"""Skill context budget (IA-1) — the sum of all SKILL.md bodies is capped at 100 KiB.

Independently derived from omd's own measured footprint (~58 KiB on 2026-07-11), NOT
from OMC's 64 KiB figure (that is a post-compression yardstick — do not analogize).
Lock the cap BEFORE R2 grows the bodies (same logic as G7: rule before the fleet doubles).
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
BUDGET_BYTES = 100 * 1024


def test_skill_bodies_within_budget():
    sizes = {p: p.stat().st_size for p in (ROOT / "skills").glob("*/SKILL.md")}
    total = sum(sizes.values())
    assert total <= BUDGET_BYTES, (
        f"skills/*/SKILL.md total {total} B exceeds {BUDGET_BYTES} B budget; "
        "largest: " + ", ".join(f"{p.parent.name}={s}" for p, s in sorted(sizes.items(), key=lambda kv: -kv[1])[:3])
    )
