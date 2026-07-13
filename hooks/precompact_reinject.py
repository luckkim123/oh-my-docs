"""OMD notepad compaction-survival hook (G2). stdlib only, fail-open.

One file, two registrations (hook_event_name branches):
- PreCompact          : PRUNE — if .omd/notepad.md exceeds MAX_BYTES, trim the
  '## Working Notes' section to its newest KEEP_LINES lines (atomic os.replace,
  ST-1). '## Priority Context' and '## Manual' are NEVER touched. Emits nothing.
- SessionStart(compact): REINJECT — emit the '## Priority Context' section as
  additionalContext so pipeline-critical constraints (original-destruction ban,
  current gate, slug) survive the compaction boundary. docs-pilot writes that
  section on entry (skills/docs-pilot Execution_Policy); contract card:
  references/notepad.md.
Advisory infrastructure only — a broken notepad must never block anything.
"""
import json
import os
import sys
import tempfile

PRIORITY = "## Priority Context"
WORKING = "## Working Notes"
MANUAL = "## Manual"
MAX_BYTES = 16 * 1024
KEEP_LINES = 40


def _split_sections(text):
    """[(heading_or_None, [lines])] — preserves order and non-section preamble."""
    sections, current = [], (None, [])
    for line in text.splitlines():
        if line.startswith("## "):
            sections.append(current)
            current = (line.strip(), [])
        else:
            current[1].append(line)
    sections.append(current)
    return sections


def _section_body(text, heading):
    for head, lines in _split_sections(text):
        if head == heading:
            return "\n".join(lines).strip()
    return ""


def reinject(notepad_path):
    if not os.path.isfile(notepad_path):
        return
    with open(notepad_path, encoding="utf-8", errors="replace") as f:
        priority = _section_body(f.read(), PRIORITY)
    if priority:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    "[OMD notepad] compaction 이전의 Priority Context 재주입:\n"
                    + priority),
            },
        }))


def prune(notepad_path):
    if not os.path.isfile(notepad_path):
        return
    if os.path.getsize(notepad_path) <= MAX_BYTES:
        return
    with open(notepad_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    out = []
    for head, lines in _split_sections(text):
        if head == WORKING and len(lines) > KEEP_LINES:
            kept = lines[-KEEP_LINES:]
            lines = ["<!-- pruned by precompact_reinject (G2): oldest working "
                     "notes trimmed -->"] + kept
        if head is not None:
            out.append(head)
        out.extend(lines)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(notepad_path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        os.replace(tmp, notepad_path)  # ST-1: atomic, never open+truncate
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main():
    try:
        payload = json.load(sys.stdin)
        notepad = os.path.join(payload.get("cwd") or os.getcwd(), ".omd", "notepad.md")
        event = payload.get("hook_event_name", "")
        if event == "SessionStart":
            reinject(notepad)
        elif event == "PreCompact":
            prune(notepad)
    except Exception:
        pass  # fail-open — advisory infrastructure must never block
    return 0


if __name__ == "__main__":
    sys.exit(main())
