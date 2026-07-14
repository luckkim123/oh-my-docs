"""omd wiki query helper (KN-2·KN-3·KN-4) — stdlib-only OPTIONAL utility, NOT a registered hook.

Fulfils the CJK bi-gram keyword-matching contract references/wiki/README.md has
promised (a contract-debt repayment, not a new feature). Three-tier tokenizer:
Latin words / CJK 1+2-grams / other-script whitespace fallback. Deterministic
only — no embeddings, ever (hard invariant). Any stage may shell out:
    python3 query_helper.py tokenize <text>
    python3 query_helper.py match <category-dir> <text>
    python3 query_helper.py slug <title>
Plain LLM grep stays a valid degrade path when python3 is unavailable.
"""
import hashlib
import os
import re
import sys
import unicodedata

_LATIN = re.compile(r"[a-z0-9]+")
# Hangul syllables + jamo + compat jamo, CJK unified ideographs, Hiragana/Katakana
# (escaped ranges only — literal CJK range chars invite encoding bugs)
_CJK = re.compile(
    "[" "\\uac00-\\ud7a3"   # Hangul syllables
        "\\u1100-\\u11ff"   # Hangul jamo
        "\\u3130-\\u318f"   # Hangul compat jamo
        "\\u4e00-\\u9fff"   # CJK unified ideographs
        "\\u3040-\\u30ff"   # Hiragana + Katakana
    "]+")


def tokenize(text):
    """3-tier deterministic token set: latin words / CJK 1+2-grams / other fallback."""
    text = unicodedata.normalize("NFKC", text or "").lower()
    tokens = set(_LATIN.findall(text))
    for run in _CJK.findall(text):
        tokens.update(run)  # 1-grams
        tokens.update(run[i:i + 2] for i in range(len(run) - 1))  # 2-grams
    leftover = _CJK.sub(" ", _LATIN.sub(" ", text))
    tokens.update(t for t in leftover.split() if t)
    return tokens


def safe_wiki_path(wiki_root, category, filename):
    """KN-3: validate a wiki write target BEFORE any Write into .omd/wiki/**.
    Rejects separators, '..' and dot-prefixed segments, then re-checks the
    resolved path still sits under wiki_root (belt and braces)."""
    for part in (category, filename):
        if (not part or "/" in part or "\\" in part or ".." in part
                or part.startswith(".")):
            raise ValueError(f"unsafe wiki path segment: {part!r}")
    root = os.path.realpath(wiki_root)
    target = os.path.realpath(os.path.join(root, category, filename))
    if os.path.commonpath([root, target]) != root:
        raise ValueError(f"resolved path escapes wiki root: {target}")
    return os.path.join(wiki_root, category, filename)


def title_to_slug(title):
    """KN-4: English-keyword slug even for Korean topics (paraphrase to English
    keywords upstream when possible). No ASCII token at all -> deterministic
    sha256 8-hex fallback. The hash fallback lives HERE, in write code — an LLM
    must never improvise a hash (non-deterministic across sessions)."""
    words = re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKC", title or "").lower())
    slug = "-".join(words)[:64].strip("-")
    if slug:
        return slug + ".md"
    digest = hashlib.sha256((title or "").encode("utf-8")).hexdigest()[:8]
    return f"note-{digest}.md"


def match(store_dir, query, limit=10):
    """Rank a category dir's .md files by token overlap with the query.
    Deterministic (overlap desc, then name asc); [] when the dir is absent."""
    want = tokenize(query)
    if not want or not os.path.isdir(store_dir):
        return []
    scored = []
    for name in sorted(os.listdir(store_dir)):
        if not name.endswith(".md"):
            continue
        try:
            with open(os.path.join(store_dir, name), encoding="utf-8",
                      errors="replace") as f:
                body = f.read()
        except OSError:
            continue
        overlap = len(want & tokenize(name + "\n" + body))
        if overlap:
            scored.append((-overlap, name))
    return [(name, -neg) for neg, name in sorted(scored)[:limit]]


def main(argv):
    if len(argv) >= 2 and argv[0] == "tokenize":
        print("\n".join(sorted(tokenize(" ".join(argv[1:])))))
        return 0
    if len(argv) >= 3 and argv[0] == "match":
        for name, score in match(argv[1], " ".join(argv[2:])):
            print(f"{score}\t{name}")
        return 0
    if len(argv) >= 2 and argv[0] == "slug":
        print(title_to_slug(" ".join(argv[1:])))
        return 0
    print("usage: query_helper.py tokenize <text> | match <dir> <text> | slug <title>",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
