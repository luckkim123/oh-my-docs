"""omd wiki lint (G3) — report-only auditor for a .omd/wiki/ store. stdlib only.

ADAPTED from the omx wiki linter (omx-core wiki/lint.py, W5 "never auto-fix"):
omd wiki notes are free-form .md WITHOUT a machine schema (references/wiki/README.md),
so frontmatter is never required — only the optional `confidence:` marker is
inspected, staleness keys on file mtime, and the orphan check fires only when the
store actually uses [[wikilinks]] (a link-less store would false-flag every note).
Near-duplicate = filename-token Jaccard >= 0.5 (omx-measured threshold, borrowed).
Omx checks NOT ported, deliberately: `contradiction-candidate` (keys on omx's
tag vocabulary) and `low-confidence`/`low-quality` (key on a confidence enum +
quality_score) — omd notes carry neither field, so the checks cannot apply.
NEVER gates: exit code is always 0 — docs-learn reads the report, a human decides.
"""
import argparse
import datetime
import os
import re
import sys

CATEGORIES = ("convention", "pattern", "decision", "reference")
# Family wiki-status convention (soft/warn only — omd has no gating boundary):
# `needs-revision` = a measured style/spec correction recorded but not yet applied;
# `resolved` = terminal. Absent = not actionable (every existing note).
STATUS_VALUES = ("needs-revision", "resolved")
# [^\S\n] = whitespace but NOT a newline: a bare `status:` (no value) must not let
# \s* cross the line and capture the next key (e.g. `blocked-on:`) as the value.
# An empty status simply produces no match -> treated as "no status" (matches the
# line-anchored grep fallback).
_STATUS = re.compile(r"^status:[^\S\n]*(\S+)", re.M)
WIKILINK = re.compile(r"\[\[([^\]|#]+)")
NEAR_DUP_JACCARD = 0.5
_STOP = frozenset({"the", "a", "an", "and", "or", "of", "to", "is", "in", "on",
                   "md", "spec", "notes", "note"})


def _tokens(name):
    raw = name[:-3] if name.endswith(".md") else name
    return {t for t in re.split(r"[-_\s]+", raw.lower()) if t and t not in _STOP}


def _mtime_dt(path):
    return datetime.datetime.fromtimestamp(os.path.getmtime(path))


def scan(root, now=None, stale_days=90, max_bytes=10240):
    """Audit the store. Returns [(severity, type, relpath, message)]. Never raises
    on content problems — a broken page is an issue, not a crash."""
    issues = []
    if not os.path.isdir(root):
        return [("info", "empty", root,
                 "no wiki store at this root (fresh project — not an error)")]
    now_dt = (datetime.datetime.fromisoformat(now) if now
              else datetime.datetime.now())

    pages = {}  # relpath -> (category, stem, body)
    for entry in sorted(os.listdir(root)):
        full = os.path.join(root, entry)
        if os.path.isfile(full) and entry.endswith(".md"):
            issues.append(("warning", "misplaced", entry,
                           f"expected under one of {CATEGORIES}"))
        elif os.path.isdir(full) and entry not in CATEGORIES:
            issues.append(("warning", "unknown-category", entry,
                           f"not one of {CATEGORIES}"))
        elif os.path.isdir(full):
            for name in sorted(os.listdir(full)):
                if not name.endswith(".md"):
                    continue
                rel = os.path.join(entry, name)
                try:
                    with open(os.path.join(full, name), encoding="utf-8",
                              errors="replace") as f:
                        body = f.read()
                except OSError as exc:
                    issues.append(("error", "unreadable", rel, str(exc)))
                    continue
                pages[rel] = (entry, name[:-3], body)

    # per-page checks
    stems = {stem for _, stem, _ in pages.values()}
    link_culture = any(WIKILINK.search(body) for _, _, body in pages.values())
    inbound = {stem: 0 for stem in stems}
    for rel, (cat, stem, body) in pages.items():
        path = os.path.join(root, rel)
        age = (now_dt - _mtime_dt(path)).days
        if age > stale_days:
            issues.append(("info", "stale", rel,
                           f"not touched in {age} days (> {stale_days})"))
        size = os.path.getsize(path)
        if size > max_bytes:
            issues.append(("warning", "oversized", rel,
                           f"{size} bytes > {max_bytes}"))
        if cat == "convention" and not re.search(r"^confidence:", body, re.M):
            issues.append(("info", "missing-confidence", rel,
                           "convention note without a confidence: marker"))
        status_m = _STATUS.search(body)
        if status_m:
            value = status_m.group(1)
            if value == "needs-revision":
                # keyword-independent enumeration: an open correction must ride
                # every docs-verify/docs-learn pass until resolved.
                issues.append(("warning", "open-revision", rel,
                               "open needs-revision — apply the correction or resolve it"))
            elif value not in STATUS_VALUES:
                # a typo'd status silently leaves the enumeration -> flag it.
                issues.append(("warning", "unknown-status", rel,
                               f"status {value!r} not in {STATUS_VALUES}"))
        for target in WIKILINK.findall(body):
            target = target.strip()
            if target in stems:
                inbound[target] += 1
            else:
                issues.append(("warning", "broken-ref", rel,
                               f"link target {target!r} does not exist"))

    # orphan — only when the store actually links (PD-2)
    if link_culture:
        for rel, (cat, stem, body) in sorted(pages.items()):
            path = os.path.join(root, rel)
            fresh = (now_dt - _mtime_dt(path)).days <= stale_days // 2
            if inbound.get(stem, 0) == 0 and not fresh:
                issues.append(("info", "orphan", rel, "no page links to this page"))

    # near-duplicate within a category (slug-fork failure mode)
    by_cat = {}
    for rel, (cat, stem, _) in pages.items():
        by_cat.setdefault(cat, []).append((rel, _tokens(stem)))
    for cat, items in sorted(by_cat.items()):
        items.sort()
        for i in range(len(items)):
            rel_a, tok_a = items[i]
            if not tok_a:
                continue
            for j in range(i + 1, len(items)):
                rel_b, tok_b = items[j]
                union = tok_a | tok_b
                if union and len(tok_a & tok_b) / len(union) >= NEAR_DUP_JACCARD:
                    issues.append(("info", "near-duplicate", rel_a,
                                   f"filename overlaps {rel_b!r} — read both; "
                                   f"if one topic, merge by hand"))
    return issues


def main(argv=None):
    ap = argparse.ArgumentParser(description="omd wiki lint — report-only, exit 0")
    ap.add_argument("--root", default=os.path.join(".omd", "wiki"))
    ap.add_argument("--now", default=None, help="ISO timestamp (tests inject this)")
    ap.add_argument("--stale-days", type=int, default=90)
    ap.add_argument("--max-bytes", type=int, default=10240)
    args = ap.parse_args(argv)
    issues = scan(args.root, now=args.now, stale_days=args.stale_days,
                  max_bytes=args.max_bytes)
    for sev, typ, rel, msg in issues:
        print(f"{sev:7s} {typ:18s} {rel} — {msg}")
    print(f"total: {len(issues)} issue(s) — report-only; nothing was modified")
    return 0  # ALWAYS — lint never gates (W5)


if __name__ == "__main__":
    sys.exit(main())
