"""references/snippets/integrity.py — OOXML zip-level closure checks (pptx.md's 5-way
closure scan). Fully pure-logic (stdlib zipfile/xml.etree) — no skip, runs unconditionally
on clean CI. In-memory zips only, one planted defect per test.
"""
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "references" / "snippets"))
import integrity  # noqa: E402


def _zip_bytes(parts: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in parts.items():
            zf.writestr(name, content)
    return buf.getvalue()


CONTENT_TYPES_CLEAN = (
    '<?xml version="1.0"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/ppt/presentation.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
    "</Types>"
)

ROOT_RELS_CLEAN = (
    '<?xml version="1.0"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="officeDocument" Target="ppt/presentation.xml"/>'
    "</Relationships>"
)

PRESENTATION_CLEAN = (
    '<?xml version="1.0"?>'
    '<p:presentation xmlns:p="p" xmlns:r="r">'
    '<p:sldMasterIdLst><p:sldMasterId r:id="rId1"/></p:sldMasterIdLst>'
    '<p:sldIdLst><p:sldId r:id="rId2"/></p:sldIdLst>'
    "</p:presentation>"
)

PRESENTATION_RELS_CLEAN = (
    '<?xml version="1.0"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    '<Relationship Id="rId2" Type="slide" Target="slides/slide1.xml"/>'
    "</Relationships>"
)

SLIDE_MASTER_CLEAN = (
    '<?xml version="1.0"?>'
    '<p:sldMaster xmlns:p="p" xmlns:r="r">'
    '<p:sldLayoutIdLst><p:sldLayoutId r:id="rId1"/></p:sldLayoutIdLst>'
    "</p:sldMaster>"
)

SLIDE_MASTER_RELS_CLEAN = (
    '<?xml version="1.0"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    "</Relationships>"
)

SLIDE_CLEAN = '<?xml version="1.0"?><p:sld xmlns:p="p" xmlns:r="r"/>'
SLIDE_LAYOUT_CLEAN = '<?xml version="1.0"?><p:sldLayout xmlns:p="p"/>'


def _clean_parts():
    return {
        "[Content_Types].xml": CONTENT_TYPES_CLEAN,
        "_rels/.rels": ROOT_RELS_CLEAN,
        "ppt/presentation.xml": PRESENTATION_CLEAN,
        "ppt/_rels/presentation.xml.rels": PRESENTATION_RELS_CLEAN,
        "ppt/slideMasters/slideMaster1.xml": SLIDE_MASTER_CLEAN,
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": SLIDE_MASTER_RELS_CLEAN,
        "ppt/slideLayouts/slideLayout1.xml": SLIDE_LAYOUT_CLEAN,
        "ppt/slides/slide1.xml": SLIDE_CLEAN,
    }


def test_clean_fixture_passes_every_checker():
    path = io.BytesIO(_zip_bytes(_clean_parts()))
    assert integrity.zip_crc_ok(path) is True
    assert integrity.no_duplicate_parts(path) == []
    assert integrity.xml_wellformed_all(path) == []
    assert integrity.find_dangling_rels(path) == []
    assert integrity.find_unregistered_rids(path) == []
    assert integrity.find_content_types_gaps(path) == []
    assert integrity.find_orphan_master(path) == []


def test_zip_crc_ok_detects_corruption():
    raw = bytearray(_zip_bytes(_clean_parts()))
    # Flip a byte inside the local file data region (well past the header) to corrupt CRC.
    raw[-40] ^= 0xFF
    path = io.BytesIO(bytes(raw))
    assert integrity.zip_crc_ok(path) is False


def test_no_duplicate_parts_detects_duplicate_entry():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ppt/slides/slide1.xml", SLIDE_CLEAN)
        zf.writestr("ppt/slides/slide1.xml", SLIDE_CLEAN)
    dupes = integrity.no_duplicate_parts(buf)
    assert dupes == ["ppt/slides/slide1.xml"]


def test_xml_wellformed_all_detects_malformed_xml():
    parts = _clean_parts()
    parts["ppt/slides/slide1.xml"] = "<p:sld><unclosed></p:sld>"
    path = io.BytesIO(_zip_bytes(parts))
    bad = integrity.xml_wellformed_all(path)
    assert any(name == "ppt/slides/slide1.xml" for name, _err in bad)


def test_find_dangling_rels_detects_missing_target():
    parts = _clean_parts()
    parts["ppt/_rels/presentation.xml.rels"] = (
        '<?xml version="1.0"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="slideMaster" Target="slideMasters/slideMaster1.xml"/>'
        '<Relationship Id="rId2" Type="slide" Target="slides/MISSING.xml"/>'
        "</Relationships>"
    )
    path = io.BytesIO(_zip_bytes(parts))
    dangling = integrity.find_dangling_rels(path)
    assert any("MISSING.xml" in d for d in dangling)


def test_find_unregistered_rids_detects_undefined_rid():
    parts = _clean_parts()
    parts["ppt/presentation.xml"] = (
        '<?xml version="1.0"?>'
        '<p:presentation xmlns:p="p" xmlns:r="r">'
        '<p:sldMasterIdLst><p:sldMasterId r:id="rId1"/></p:sldMasterIdLst>'
        '<p:sldIdLst><p:sldId r:id="rId99"/></p:sldIdLst>'
        "</p:presentation>"
    )
    path = io.BytesIO(_zip_bytes(parts))
    unregistered = integrity.find_unregistered_rids(path)
    assert any("rId99" in u for u in unregistered)


def test_find_content_types_gaps_detects_missing_override():
    parts = _clean_parts()
    parts["[Content_Types].xml"] = (
        '<?xml version="1.0"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        "</Types>"
    )
    path = io.BytesIO(_zip_bytes(parts))
    gaps = integrity.find_content_types_gaps(path)
    assert gaps  # ppt/presentation.xml's .xml extension is no longer covered


def test_find_orphan_master_detects_orphan_layout_id():
    parts = _clean_parts()
    parts["ppt/slideMasters/slideMaster1.xml"] = (
        '<?xml version="1.0"?>'
        '<p:sldMaster xmlns:p="p" xmlns:r="r">'
        '<p:sldLayoutIdLst><p:sldLayoutId r:id="rId99"/></p:sldLayoutIdLst>'
        "</p:sldMaster>"
    )
    path = io.BytesIO(_zip_bytes(parts))
    orphans = integrity.find_orphan_master(path)
    assert any("rId99" in o for o in orphans)
