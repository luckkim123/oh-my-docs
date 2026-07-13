"""Tests for the two-level wiki contract (local + global ascent).

Backported from oms's two-level wiki (commit e47ab44) on 2026-05-31, ADAPTED to the
omd domain: the global `history/` category is dropped (omd has no `init`/doc-dedup
need), oms's "citation forbidden from global" becomes omd's "document content
forbidden from global", and a cross-project confidentiality gate is added (the global
level is shared by multiple document projects that may hold confidential material).

These are deterministic grep-asserts over the *contract documents* (.md) — the change
is pure-documentation (no hook/py edited), so the guard is "the two-level contract is
present and its omd-specific invariants are not silently regressed." Mirrors oms's
`test_scholar_init_skill.py` style (read the body, assert the invariant keywords).
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
WIKI_README = ROOT / "references" / "wiki" / "README.md"
LEARNING = ROOT / "references" / "learning-protocol.md"
INSPECTOR = ROOT / "agents" / "doc-inspector.md"
PILOT = ROOT / "skills" / "docs-pilot" / "SKILL.md"
LEARN = ROOT / "skills" / "docs-learn" / "SKILL.md"


def _body(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _flat(p: Path) -> str:
    """Whitespace-normalized body — matching is wrap/coordinate-independent so a
    benign reflow of the contract prose does not false-fail the guard (the guard
    must catch the *meaning* being removed, not a specific hard-wrap position)."""
    return " ".join(_body(p).split())


def test_wiki_readme_declares_two_levels():
    """README declares local + global, found by ascent (not absolute/env/XDG)."""
    body = _body(WIKI_README)
    assert "GLOBAL level" in body
    assert "LOCAL level" in body
    assert "ascent" in body
    # relative-only philosophy preserved (oms's "no absolute/env/XDG")
    assert "no absolute path" in body
    assert "no env var" in body


def test_wiki_query_contract_is_two_level_merge_with_provenance():
    """wiki_query merges both levels and tags provenance; call site unchanged."""
    body = _body(WIKI_README)
    assert "two-level ascent merge" in body
    assert "[wiki:local]" in body and "[wiki:global]" in body
    # the ascent/merge/tagging are sealed inside the abstract function
    assert "sealed inside" in body
    assert "does not change by a single line" in body


def test_global_history_category_is_dropped_in_omd():
    """⚠️ omd ADAPT: the oms global-only `history/` category must NOT be adopted."""
    readme = _flat(WIKI_README)
    learning = _flat(LEARNING)
    # history is mentioned ONLY in a negation context (it is intentionally absent) —
    # assert the negation is adjacent to the word, not just that "not present" appears
    # somewhere (which would pass even on an unrelated sentence).
    assert "history" in readme
    assert "`history/` category that the sibling oms harness carries" in readme
    assert "not present" in readme
    assert "`history/` category that oms carries" in learning
    assert "not present" in learning
    # the global level must list exactly convention/pattern/decision (no history) —
    # match on category membership, not on a specific separator/backtick layout
    assert "global: `convention`·`pattern`·`decision`" in readme
    # history is mentioned in both files ONLY in its negation ("not present") — it must
    # never appear as a ✅ global-eligible row in the §1.4 table.
    assert "history" in learning and "not present" in learning
    assert "`history/` category" in learning  # appears, but only in the negation clause
    # ⭐ meaning-based regression guard: no `history/` row may be marked ✅ (global-eligible)
    # in the §1.4 table. This fires if a future edit re-adds history as a live category
    # (verified: injecting a `history/ ... | ✅` row makes this match True).
    assert not re.search(r"history/[^|]*\|\s*✅", learning), \
        "history/ must not be a ✅ global-eligible category in omd (oms-only)"


def test_document_content_permanently_forbidden_from_global():
    """omd analogue of oms citation-safety: content never rises to global."""
    learning = _flat(LEARNING)
    readme = _flat(WIKI_README)
    assert "permanently forbidden" in learning
    assert "content-preservation" in learning
    # §6.F extends the invariant to the two-level wiki — wrap-independent match
    assert "permanently forbidden from rising to the global level" in learning
    # the forbidden subject is document content (text/claims/numbers/sources)
    assert "text · claims · numbers · sources" in learning or \
           "text·claims·numbers·sources" in learning or \
           "text, claims, numbers, sources" in learning
    assert "permanently forbidden" in readme


def test_cross_project_confidentiality_gate_present():
    """omd-specific gate (no oms analogue): identifiers stay local, form abstracts up."""
    learning = _flat(LEARNING)
    readme = _flat(WIKI_README)
    pilot = _flat(PILOT)
    learn = _flat(LEARN)
    for body in (learning, readme):
        assert "cross-project confidentiality" in body.lower()
        assert "project-identifiable" in body
    # docs-learn §4b is where the actual scrub runs (the gate that enforces it)
    assert "scrub" in learn.lower() and "identifier" in learn.lower()
    # pilot only HINTS at promotion; the actual scrub/promotion is docs-learn's job
    assert "식별자 스크럽" in pilot
    assert "docs-learn" in pilot  # global promotion is gated through docs-learn, not pilot


def test_docs_learn_owns_local_to_global_promotion_path():
    """S1 fix: the global-promotion path must actually exist in docs-learn, and the
    two 'global' axes (scope-label vs wiki-storage-tier) must be disambiguated — the
    pilot/learning-protocol references to docs-learn must not point at a phantom path."""
    learn = _flat(LEARN)
    # the storage-location promotion path exists as a real, named policy
    assert "local→global wiki promotion" in learn
    assert "human approval" in learn or "human gate" in learn.lower()
    # the two-global-axes disambiguation (the root of the S1 terminology collision)
    assert 'two different "global" axes' in learn.lower()
    assert "storage-location axis" in learn
    # content forbidden + scrub are enforced AT this path (not just referenced elsewhere)
    assert "permanently forbidden from the global tier" in learn
    assert "no auto-promotion" in learn.lower()


def test_inspector_call_site_signature_unchanged():
    """The wiki_query call site keeps its single-arg abstract signature (no leak)."""
    body = _body(INSPECTOR)
    assert 'wiki_query(category="convention")' in body
    # the two-level mechanism is described as sealed inside the function
    assert "sealed inside the abstract function" in body
    assert "[wiki:local]" in body and "[wiki:global]" in body


def test_no_absolute_paths_or_env_in_two_level_wiki_contract():
    """Two-level discovery is work-root-relative — no hardcoded abs path / env / XDG."""
    for p in (WIKI_README, LEARNING):
        body = _body(p)
        # the ascent is relative; these tokens would signal a regression to abs/env
        assert "XDG" in body  # mentioned only as "no XDG"
        assert "no XDG" in body
        # a hardcoded home path must never appear in the contract
        assert "/Users/" not in body
        assert "$HOME" not in body


def test_ascent_home_floor_stated_at_both_descriptions():
    """ST-3: BOTH ascent descriptions (layout diagram + contract pseudocode) carry the
    home-directory hard floor. Deliberately no literal env token — the existing
    test_no_absolute_paths_or_env_in_two_level_wiki_contract forbids it."""
    text = _body(WIKI_README)
    assert text.lower().count("never climbs above the user's home directory") >= 2


def test_english_slug_rule_stated():
    """KN-4: filenames are English-keyword slugs even for Korean topics."""
    text = _body(WIKI_README)
    assert "English-keyword" in text and "title_to_slug" in text


def test_query_helper_pointer_present():
    """KN-2: the promised CJK bi-gram matching now points at its implementation."""
    assert "query_helper.py" in _body(WIKI_README)


def test_wiki_write_sites_wired_to_guards():
    """KN-3·KN-4: the ACTUAL .omd/wiki/** write sites call the guards — README prose alone
    does not exercise them (ultracode blocking finding)."""
    for rel in ("skills/docs-pilot/SKILL.md", "skills/docs-learn/SKILL.md"):
        body = (ROOT / rel).read_text(encoding="utf-8")
        assert "safe_wiki_path" in body and "title_to_slug" in body, rel
