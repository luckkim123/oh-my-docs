"""Canonical soffice/pdftoppm render recipe + pdf page count.
Data file, copy/adapt into your own per-job build script (see references/snippets/README.md) —
never imported by an agent at runtime, only by this repo's own test suite.

Referenced by: references/formats/{pptx,docx,xlsx}.md render recipes, agents/doc-builder.md
step 7, agents/doc-verifier.md step 3.
"""
import shutil
import subprocess
from pathlib import Path


def resolve_tool(name: str) -> str:
    """Cross-platform `command -v`/`where` resolution. Never hardcode an absolute binary
    path (every office card's Engine section repeats this rule) — raise with an install
    hint instead of silently skipping the render/verify gate."""
    path = shutil.which(name)
    if path is None:
        raise FileNotFoundError(
            f"{name!r} not found on PATH. Install it and retry "
            f"(e.g. LibreOffice for `soffice`, poppler for `pdftoppm`)."
        )
    return path


def soffice_to_pdf(src_path, outdir) -> Path:
    """`soffice --headless --convert-to pdf --outdir <outdir> <src_path>`. Raises with the
    captured stderr on nonzero exit."""
    soffice = resolve_tool("soffice")
    src_path = Path(src_path)
    outdir = Path(outdir)
    proc = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(src_path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"soffice convert failed (exit {proc.returncode}): {proc.stderr}")
    return outdir / (src_path.stem + ".pdf")


def pdf_to_images(pdf_path, outdir, prefix, fmt="png", dpi=150) -> list[Path]:
    """`pdftoppm -<fmt> -r <dpi> <pdf_path> <outdir>/<prefix>`.
    `fmt` is caller-supplied, never silently defaulted: docx.md documents that
    `soffice --convert-to png` (and `-png` through PDF) only emits page 1 for multi-page
    docs (a long-standing LibreOffice bug) — multi-page callers must pass `fmt="jpeg"`."""
    pdftoppm = resolve_tool("pdftoppm")
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_prefix = outdir / prefix
    proc = subprocess.run(
        [pdftoppm, f"-{fmt}", "-r", str(dpi), str(pdf_path), str(out_prefix)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pdftoppm failed (exit {proc.returncode}): {proc.stderr}")
    ext = "jpg" if fmt == "jpeg" else fmt
    return sorted(outdir.glob(f"{prefix}*.{ext}"))


def pdf_page_count(pdf_path) -> int:
    """`len(pypdf.PdfReader(path).pages)` — pdf.md's own recommended one-liner, given one
    home so the verify-gate's "N/N pages rendered" check has a single source."""
    import pypdf

    return len(pypdf.PdfReader(str(pdf_path)).pages)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: render.py <src.pptx|docx|xlsx> [outdir]", file=sys.stderr)
        sys.exit(2)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.parent
    pdf = soffice_to_pdf(src, out)
    print(f"pdf: {pdf}")
    images = pdf_to_images(pdf, out, prefix=src.stem, fmt="jpeg")
    print(f"images: {images}")
    print(f"page count: {pdf_page_count(pdf)}")
