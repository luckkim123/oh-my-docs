"""Canonical OOXML zip-level integrity checks — the pptx.md "5-way closure scan".
Data file, copy/adapt into your own per-job verify script (see references/snippets/README.md) —
never imported by an agent at runtime, only by this repo's own test suite.
Stdlib only (zipfile, xml.etree.ElementTree, collections.Counter, re) — no optional deps.

Referenced by: references/formats/pptx.md closure-scan section (all 5 checks),
agents/doc-verifier.md Integrity gate rows (zip CRC / dangling rels / orphan master).
"""
import fnmatch
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

RID_ATTR_RE = re.compile(r'r:(?:embed|link|id)="(rId\d+)"')


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _rels_ids(zf: zipfile.ZipFile, rels_name: str) -> set:
    """Every Relationship Id defined in a given .rels part (empty set if absent/malformed)."""
    if rels_name not in zf.namelist():
        return set()
    try:
        root = ET.fromstring(zf.read(rels_name))
    except ET.ParseError:
        return set()
    return {rel.get("Id") for rel in root if _local(rel.tag) == "Relationship" and rel.get("Id")}


def _rels_base(rels_name: str) -> str:
    """OPC rule: a Target in `<dir>/_rels/<name>.rels` is relative to `<dir>`
    (root `_rels/.rels` → base = '')."""
    return posixpath.dirname(posixpath.dirname(rels_name))


def zip_crc_ok(path) -> bool:
    """`ZipFile.testzip() is None`."""
    with zipfile.ZipFile(path) as zf:
        return zf.testzip() is None


def no_duplicate_parts(path) -> list:
    """`Counter(namelist())`, names with count > 1 (empty = pass)."""
    with zipfile.ZipFile(path) as zf:
        counts = Counter(zf.namelist())
    return sorted(name for name, n in counts.items() if n > 1)


def xml_wellformed_all(path, pattern: str = "*.xml") -> list:
    """`ET.fromstring` every zip entry matching `pattern`; returns `(name, error)` failures."""
    bad = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not fnmatch.fnmatch(name, pattern):
                continue
            try:
                ET.fromstring(zf.read(name))
            except ET.ParseError as e:
                bad.append((name, str(e)))
    return bad


def find_dangling_rels(path) -> list:
    """Closure-scan check (1): every `Target` in every `.rels` part resolves to an
    existing packaged part (path-normalized; `TargetMode="External"`/http(s) skipped)."""
    dangling = []
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        for name in names:
            if not name.endswith(".rels"):
                continue
            base = _rels_base(name)
            try:
                root = ET.fromstring(zf.read(name))
            except ET.ParseError:
                continue
            for rel in root:
                if _local(rel.tag) != "Relationship":
                    continue
                if rel.get("TargetMode") == "External":
                    continue
                target = rel.get("Target", "")
                if target.startswith(("http://", "https://")):
                    continue
                resolved = target.lstrip("/") if target.startswith("/") else posixpath.normpath(
                    posixpath.join(base, target)
                )
                if resolved not in names:
                    dangling.append(f"{name} -> {target} (missing {resolved})")
    return sorted(dangling)


def find_unregistered_rids(path) -> list:
    """Closure-scan check (2): every in-body `r:(embed|link|id)="rIdN"` across all
    `ppt/**.xml` parts is defined in that part's own `_rels/<partname>.rels`."""
    unregistered = []
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        for name in names:
            if not (name.startswith("ppt/") and name.endswith(".xml")) or name.endswith(".rels"):
                continue
            text = zf.read(name).decode("utf-8", errors="replace")
            rids = set(RID_ATTR_RE.findall(text))
            if not rids:
                continue
            rels_name = posixpath.join(
                posixpath.dirname(name), "_rels", posixpath.basename(name) + ".rels"
            )
            registered = _rels_ids(zf, rels_name)
            for rid in sorted(rids - registered):
                unregistered.append(f"{name}: {rid} not in {rels_name}")
    return sorted(unregistered)


def find_content_types_gaps(path) -> list:
    """Closure-scan check (3): every packaged part's extension is covered by a
    `<Default Extension>` or an `<Override PartName>`, and every `<Override PartName>`
    resolves to a part that still exists in the zip."""
    gaps = []
    with zipfile.ZipFile(path) as zf:
        names = {n for n in zf.namelist() if not n.endswith("/")}
        try:
            root = ET.fromstring(zf.read("[Content_Types].xml"))
        except (KeyError, ET.ParseError):
            return ["[Content_Types].xml missing or malformed"]
        defaults, overrides = set(), set()
        for el in root:
            tag = _local(el.tag)
            if tag == "Default":
                ext = el.get("Extension", "").lower()
                if ext:
                    defaults.add(ext)
            elif tag == "Override":
                pn = el.get("PartName", "")
                if pn:
                    overrides.add(pn.lstrip("/"))
        for pn in sorted(overrides):
            if pn not in names:
                gaps.append(f"Override PartName not packaged: /{pn}")
        for name in sorted(names - {"[Content_Types].xml"}):
            if name in overrides:
                continue
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext not in defaults:
                gaps.append(f"part not covered by Default/Override: {name}")
    return gaps


def find_orphan_master(path) -> list:
    """Closure-scan checks (4)/(5): every `presentation.xml` `sldMasterId`/`notesMasterId`/
    `handoutMasterId` r:id resolves in `presentation.xml.rels`, and every `<p:sldLayoutId
    r:id>` in each `slideMaster` resolves in that master's own rels."""
    orphans = []
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        if "ppt/presentation.xml" in names:
            text = zf.read("ppt/presentation.xml").decode("utf-8", errors="replace")
            registered = _rels_ids(zf, "ppt/_rels/presentation.xml.rels")
            for tag in ("sldMasterId", "notesMasterId", "handoutMasterId"):
                for rid in re.findall(rf'<p:{tag}\b[^>]*\br:id="(rId\d+)"', text):
                    if rid not in registered:
                        orphans.append(
                            f"ppt/presentation.xml: {tag} {rid} not in presentation.xml.rels"
                        )
        for name in sorted(names):
            if not (name.startswith("ppt/slideMasters/") and name.endswith(".xml")):
                continue
            if "_rels" in name:
                continue
            text = zf.read(name).decode("utf-8", errors="replace")
            layout_rids = re.findall(r'<p:sldLayoutId\b[^>]*\br:id="(rId\d+)"', text)
            rels_name = posixpath.join(
                posixpath.dirname(name), "_rels", posixpath.basename(name) + ".rels"
            )
            registered = _rels_ids(zf, rels_name)
            for rid in sorted(set(layout_rids) - registered):
                orphans.append(f"{name}: sldLayoutId {rid} not in {rels_name}")
    return orphans


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: integrity.py <deck.pptx>", file=sys.stderr)
        sys.exit(2)
    target = sys.argv[1]
    checks = [
        ("zip CRC", lambda: zip_crc_ok(target)),
        ("no duplicate parts", lambda: no_duplicate_parts(target) == []),
        ("XML well-formed", lambda: xml_wellformed_all(target) == []),
        ("no dangling rels", lambda: find_dangling_rels(target) == []),
        ("no unregistered r:id", lambda: find_unregistered_rids(target) == []),
        ("no Content_Types gaps", lambda: find_content_types_gaps(target) == []),
        ("no orphan master/layout", lambda: find_orphan_master(target) == []),
    ]
    ok = True
    for label, check in checks:
        passed = check()
        ok = ok and passed
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    sys.exit(0 if ok else 1)
