"""Canonical G7 engine-version-drift check (`references/formats/README.md`'s
"Engine-drift demotion rule"). Data file, copy/adapt into your own per-job build/verify
script (see references/snippets/README.md) — never imported by an agent at runtime, only by
this repo's own test suite.

Referenced by: references/formats/README.md G7 section, agents/doc-builder.md step 8,
agents/doc-verifier.md step 8.
"""
import importlib
import re
import subprocess

# Every one of these differs from its PyPI/card name — without this map G7 silently
# reports "engine unavailable" for tools that are actually installed.
IMPORT_ALIASES = {
    "python-pptx": "pptx",
    "python-docx": "docx",
    "python-hwpx": "hwpx",
    "pillow": "PIL",
}

_ENGINE_SECTION_RE = re.compile(r"^## Engine\b(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
_TOOL_VERSION_RE = re.compile(r"`([^`]+)`\s+(\d[\d.]*)")


def parse_engine_pins(card_text: str) -> dict:
    """Extract the `## Engine` table into `{tool: pinned_version}`. Each Tool cell is
    split on `+` first (pptx.md's `` `matplotlib` 3.9.4 + `Pillow` 11.3 `` row packs two
    pairs in one cell). Segments with no version after the backticked name (presence-only
    tools like `soffice`/`pdftoppm`) are skipped by design — nothing to diff against."""
    m = _ENGINE_SECTION_RE.search(card_text)
    if not m:
        return {}
    pins = {}
    for line in m.group(1).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = line.split("|")
        if len(cells) < 2:
            continue
        for segment in cells[1].split("+"):
            seg_match = _TOOL_VERSION_RE.search(segment)
            if seg_match:
                pins[seg_match.group(1)] = seg_match.group(2)
    return pins


def live_version(spec: str):
    """`cmd:`-prefixed -> `<cmd> --version` + first `\\d+\\.\\d+`. Bare name -> alias-mapped
    `importlib.import_module(...).__version__`. Never raises — returns None on any failure
    (mirrors the cards' own D3 "UNVERIFIED (engine unavailable)" degrade)."""
    try:
        if spec.startswith("cmd:"):
            cmd = spec[len("cmd:"):]
            proc = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=10)
            m = re.search(r"\d+\.\d+", proc.stdout + proc.stderr)
            return m.group(0) if m else None
        module_name = IMPORT_ALIASES.get(spec.lower(), spec)
        mod = importlib.import_module(module_name)
        return getattr(mod, "__version__", None)
    except Exception:
        return None


def check_engine_drift(card_text: str, live_versions: dict) -> list:
    """Pinned (from `card_text`) vs. measured (`live_versions`) — mismatch lines,
    empty list = no drift."""
    pins = parse_engine_pins(card_text)
    mismatches = []
    for tool, pinned in pins.items():
        measured = live_versions.get(tool)
        if measured is not None and measured != pinned:
            mismatches.append(f"{tool}: pinned {pinned} != live {measured}")
    return mismatches


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: engine_check.py <card.md>", file=sys.stderr)
        sys.exit(2)
    text = open(sys.argv[1], encoding="utf-8").read()
    for tool, version in parse_engine_pins(text).items():
        print(f"{tool}: {version}")
