"""Distribution axiom (D8) — omd is a distributed plugin: no personal identifiers,
no absolute home paths, no machine-specific values in any shipped file.

Per spec DT-3: patterns only, NEVER literal personal tokens (writing this session's
username into the forbidden list would itself violate the axiom). Placeholders like
`/Users/<you>` are allowed (the `<` immediately after the home root marks a template).

R2 policy (user-ratified via the R2 PR): plugin.json `author` is deliberate attribution
metadata — the package.json convention — and is the ONE sanctioned identifier in shipped
files. It is name-only attribution; the pattern scans below still apply to it (no home
path, no email in the author block either).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCAN_ROOTS = ["skills", "agents", "hooks", "references", ".claude-plugin"]
SCAN_SUFFIXES = {".md", ".py", ".json", ".txt"}

HOME_PATH_RE = re.compile(r"/(?:Users|home)/(?!<)[A-Za-z0-9_.-]+")
EMAIL_RE = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+")


def shipped_files():
    for root in SCAN_ROOTS:
        for p in (ROOT / root).rglob("*"):
            if p.is_file() and p.suffix in SCAN_SUFFIXES:
                yield p


def _hits(pattern):
    out = []
    for p in shipped_files():
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if pattern.search(line):
                out.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:100]}")
    return out


def test_no_absolute_home_paths():
    hits = _hits(HOME_PATH_RE)
    assert not hits, "absolute home paths in shipped files:\n" + "\n".join(hits)


def test_no_email_addresses():
    hits = _hits(EMAIL_RE)
    assert not hits, "email addresses in shipped files:\n" + "\n".join(hits)


def test_author_field_is_intentional_attribution():
    """R2 정책: author 필드는 의도적 attribution — 존재 유지 + 패턴 스캔은 그대로 적용
    (홈경로·이메일이 author 블록에 스며들면 위 테스트들이 잡는다). 리터럴 개인 토큰은
    이 테스트에도 넣지 않는다(DT-3)."""
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    author = manifest.get("author", {})
    assert isinstance(author, dict) and author.get("name"), "author attribution should stay present"
