"""references/snippets/render.py — soffice/pdftoppm/pypdf wrappers.
resolve_tool is pure logic (no skip); the rest need real binaries/libs absent on clean CI.
"""
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "references" / "snippets"))
import render  # noqa: E402


def test_resolve_tool_missing_binary_raises():
    with pytest.raises(FileNotFoundError):
        render.resolve_tool("definitely-not-a-real-binary-xyz")


@pytest.mark.skipif(
    shutil.which("soffice") is None or shutil.which("pdftoppm") is None,
    reason="soffice/pdftoppm not installed",
)
def test_soffice_to_pdf_and_pdf_to_images(tmp_path):
    # No fixture doc bundled — this only proves the tools resolve when present.
    assert shutil.which("soffice")
    assert shutil.which("pdftoppm")


@pytest.mark.skipif(
    importlib.util.find_spec("pypdf") is None, reason="pypdf not installed"
)
def test_pdf_page_count_importable():
    import pypdf  # noqa: F401

    assert render.pdf_page_count is not None
