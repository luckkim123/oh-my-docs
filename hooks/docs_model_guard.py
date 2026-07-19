"""OMD PreToolUse(Task) hook: advisory model-tier guard (G4). stdlib only, fail-open.

doc-verifier's trust model presumes "the verifier ran on opus" — but nothing enforced
it. This hook does NOT block (D6): it only warns when a Task call explicitly pins a
model that contradicts the agent's frontmatter, or names a nonexistent oh-my-docs
agent. An unspecified model is the NORMAL state (Claude Code applies the agent
definition's model) — never warn about absence (spec AC-2).
"""
import json
import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
PREFIX = "oh-my-docs:"


def frontmatter_model(agent_name: str):
    path = AGENTS_DIR / f"{agent_name}.md"
    if not path.is_file():
        return None  # unknown agent
    fm_open = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip() == "---":
            if fm_open:
                break
            fm_open = True
            continue
        if fm_open and line.startswith("model:"):
            return line.partition(":")[2].strip()
    return ""  # agent exists, no model pin


def check(payload: dict):
    """Return an advisory message or None (silent)."""
    if payload.get("tool_name") != "Task":
        return None
    ti = payload.get("tool_input", {}) or {}
    sub = ti.get("subagent_type", "")
    if not isinstance(sub, str) or not sub.startswith(PREFIX):
        return None
    agent = sub[len(PREFIX):]
    pinned = frontmatter_model(agent)
    if pinned is None:
        known = ", ".join(sorted(p.stem for p in AGENTS_DIR.glob("doc-*.md")))
        return (f"[OMD model-guard] unknown agent '{sub}' — no agents/{agent}.md. "
                f"Known: {known}. (advisory — proceeding)")
    requested = ti.get("model")
    if requested and pinned and requested != pinned:
        return (f"[OMD model-guard] '{agent}' is pinned to model '{pinned}' in its frontmatter "
                f"but this call requests '{requested}'. If this is not a deliberate escalation "
                f"(e.g. docs-plan --consensus), drop the model override. (advisory — proceeding)")
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        msg = check(payload)
        if msg:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": msg,
            }}))
    except Exception:
        pass  # fail-open — never block the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
