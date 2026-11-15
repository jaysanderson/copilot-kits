"""Build a deck by populating the Progress corporate template (template path).

When a brand template exists, we build ON it (native branding, layouts, theme)
rather than scratch-building with build_deck.py. This copies the template, drops
its sample slides (keep with --keep-samples), then adds slides from named layouts
and fills their placeholders from a JSON content spec.

Inspect the template first to learn its layout and placeholder names:
    python scripts/build_from_template.py --inspect

Spec format (content/deck-spec.json):
    [
      {"layout": "Title Slide",
       "text": {"Title 1": "Agentic RAG for Tangerine",
                "Subtitle 2": "Answers your customers can trust"}},
      {"layout": "Title and Content",
       "text": {"Title 1": "The answer, with citations"},
       "image": {"path": "shots/demo-03.png", "left": 5.2, "top": 1.6, "width": 7.4}}
    ]
Placeholder keys match by name (as shown by --inspect) or by integer idx.

Usage:
    python scripts/build_from_template.py --spec content/deck-spec.json \
        --out decks/tangerine-progress.pptx
    python scripts/build_from_template.py --spec ... --template brand/templates/other.pptx
"""
import argparse
import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Inches

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = ROOT / "brand" / "templates" / "progress-corporate-fy26.pptx"


def drop_slides(prs):
    """Remove all existing slides (references AND parts) but keep masters,
    layouts and theme. Dropping the relationship orphans the slide part so it
    is not re-serialised - otherwise new slides collide with leftover
    slideN.xml parts and corrupt the package."""
    part = prs.part
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        rId = sldId.get(qn("r:id"))
        if rId:
            try:
                part.drop_rel(rId)
            except KeyError:
                pass
        sldIdLst.remove(sldId)


def find_layout(prs, ref):
    """Match a layout by name (case-insensitive) or by flat index across masters."""
    layouts = [ly for master in prs.slide_masters for ly in master.slide_layouts]
    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        return layouts[int(ref)]
    for ly in layouts:
        if ly.name.lower() == str(ref).lower():
            return ly
    sys.exit(f"Layout '{ref}' not found. Run --inspect to list layout names.")


def inspect(prs):
    layouts = [ly for master in prs.slide_masters for ly in master.slide_layouts]
    print(f"{len(layouts)} layouts:\n")
    for i, ly in enumerate(layouts):
        phs = ", ".join(f"[{p.placeholder_format.idx}] {p.name}"
                        for p in ly.placeholders)
        print(f"{i:3}  {ly.name!r}")
        if phs:
            print(f"     placeholders: {phs}")


def fill_slide(slide, spec):
    by_name = {p.name: p for p in slide.placeholders}
    by_idx = {p.placeholder_format.idx: p for p in slide.placeholders}
    for key, value in spec.get("text", {}).items():
        ph = by_name.get(key) or by_idx.get(int(key) if str(key).isdigit() else -1)
        if ph is None:
            print(f"  warning: no placeholder '{key}' on this slide", file=sys.stderr)
            continue
        # A list (or a \n string) becomes one paragraph per line, so bulleted
        # content layouts render real bullets, not one line-broken blob.
        lines = value if isinstance(value, list) else str(value).split("\n")
        tf = ph.text_frame
        tf.text = lines[0]
        for line in lines[1:]:
            tf.add_paragraph().text = line

    img = spec.get("image")
    if img:
        path = img["path"]
        left, top = Inches(img.get("left", 1)), Inches(img.get("top", 1.5))
        width = Inches(img["width"]) if "width" in img else None
        slide.shapes.add_picture(path, left, top, width=width)

    notes = spec.get("notes")
    if notes:
        slide.notes_slide.notes_text_frame.text = notes

# =============================================================================
# Package hygiene (added 10 Oct 2026). A .pptx is a ZIP: the corporate template carries real people's
# names, an email, user GUIDs, a stale app.xml (slide titles, counts) and its own cover thumbnail, and
# python-pptx copies all of it through untouched. The rendered slides never show it, so no slide-level
# check can see it. Every deck built on a template goes through sanitise_package() and is proved with
# audit_package() (which returns the NUMBER OF PARTS EXAMINED - zero of zero is not a pass).
# =============================================================================
import io
import posixpath
import re
import zipfile

REMOVE_PARTS = ("ppt/authors.xml", "ppt/commentAuthors.xml")
REMOVE_PREFIXES = ("ppt/changesInfos/", "ppt/comments/")
THUMB = "docProps/thumbnail.jpeg"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
THUMB_REL = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"
NON_PERSONAL = "Progress Agentic RAG GTM"


def _is_removed(name):
    return name in REMOVE_PARTS or name.startswith(REMOVE_PREFIXES)


def _read_zip(path):
    with zipfile.ZipFile(path) as z:
        return [(i, z.read(i.filename)) for i in z.infolist()]


# --- Embedded names in BINARY parts (added 12 Oct 2026) ---------------------------------------------------
# The template's layout artwork (ppt/media/*.emf) embeds an Illustrator "%%For: (<designer>)" comment. Those
# names are in NO author list, so a denylist harvested from the structured parts never contains them
# (Gabriela Perez, found 12 Oct 2026, was only ever in three EMFs), and a text-only audit cannot see them.
# So the scan below is DISCOVERY - it finds whatever name is there - and redaction never needs the name known.
FOR_RE = re.compile(rb"(%%For: \()([^)\r\n]*)(\))")


def discover_embedded_names(path):
    """{name: [parts]} for every non-blank Illustrator '%%For: (name)' comment in any part, raw bytes."""
    found = {}
    for info, data in _read_zip(path):
        for m in FOR_RE.finditer(data):
            nm = m.group(2).decode("latin-1").strip()
            if nm:
                found.setdefault(nm, []).append(info.filename)
    return found


def redact_embedded(data):
    """Length-preserving: overwrite the name inside every '%%For: (...)' with spaces. Returns (data, count)."""
    n = [0]
    def blank(m):
        if m.group(2).strip():
            n[0] += 1
        return m.group(1) + b" " * len(m.group(2)) + m.group(3)
    return FOR_RE.sub(blank, data), n[0]


def harvest_names(path):
    """Distinct person names in the structured places Office stores them (author lists, comment authors,
    change tracking, core properties). Used to build the denylist the audit scans every part for."""
    names = set()
    for info, data in _read_zip(path):
        n = info.filename
        if not n.endswith(".xml"):
            continue
        t = data.decode("utf-8", "ignore")
        if n in REMOVE_PARTS or n.startswith(REMOVE_PREFIXES):
            names.update(m.group(1) for m in re.finditer(r'\bname="([^"]+)"', t))
        if n == "docProps/core.xml":
            names.update(m.group(1) for m in re.finditer(r"<(?:dc:creator|cp:lastModifiedBy)>([^<]+)<", t))
    names.update(discover_embedded_names(path))      # discovery, not confirmation: names in no author list
    return {x for x in names if x.strip()}


class PackageAuditError(RuntimeError):
    """Raised by audit_package(strict=True) when the package carries personal data."""


def audit_package(path, deny_names=(), allowed_people=("Jay Sanderson",), strict=False):
    """Read-only. Walk EVERY part and report personal data. Returns (findings, parts_examined, text_parts_examined).
    Findings: forbidden parts present, any denylisted name in any text part, any email address, a lastModifiedBy
    or creator that is not allowed, a surviving TitlesOfParts/HeadingPairs, a thumbnail still equal to nothing
    we generated is NOT judged here (see sanitise_package) - only presence is reported by the caller.
    BINARY parts are scanned in raw bytes too (a denylisted name as UTF-8 or UTF-16LE, and ANY non-blank
    Illustrator '%%For: (name)' whether or not the name is on the denylist). strict=True raises
    PackageAuditError on any finding instead of returning it."""
    findings, parts, text_parts = [], 0, 0
    deny = [n for n in deny_names if n.strip()]
    for info, data in _read_zip(path):
        parts += 1
        n = info.filename
        for m in FOR_RE.finditer(data):
            if m.group(2).strip():
                findings.append(("embedded-name", f"{n}: %%For: ({m.group(2).decode('latin-1').strip()})"))
        if not n.endswith((".xml", ".rels")):
            for nm in deny:
                if nm.encode("utf-8") in data or nm.encode("utf-16le") in data:
                    findings.append(("name-in-binary-part", f"{n}: {nm}"))
        if _is_removed(n):
            findings.append(("forbidden-part", n))
        if n.endswith((".xml", ".rels")):
            text_parts += 1
            t = data.decode("utf-8", "ignore")
            for e in sorted(set(EMAIL_RE.findall(t))):
                findings.append(("email", f"{n}: {e}"))
            for nm in deny:
                if nm in t:
                    findings.append(("name", f"{n}: {nm}"))
            if n == "docProps/core.xml":
                for tag in ("dc:creator", "cp:lastModifiedBy"):
                    m = re.search(rf"<{tag}>([^<]*)<", t)
                    if m and m.group(1) not in allowed_people and m.group(1) != NON_PERSONAL:
                        findings.append(("person-in-core-properties", f"{tag}={m.group(1)}"))
            if n == "docProps/app.xml" and ("<TitlesOfParts>" in t or "<HeadingPairs>" in t):
                findings.append(("stale-app-xml", "TitlesOfParts/HeadingPairs present"))
    if strict and findings:
        raise PackageAuditError(f"{len(findings)} findings, first: {findings[:3]}")
    return findings, parts, text_parts


TEMPLATE_CORE = {"title": "Your  Progress", "created": "2025-11-17T19:49:51Z", "modified": "2026-05-07T19:02:09Z"}


def sanitise_package(path, author="Jay Sanderson", slide_count=None, thumbnail_png=None,
                     last_modified_by=NON_PERSONAL, title=None):
    """Strip personal and stale template metadata from a saved .pptx IN PLACE. Returns a dict of what was removed
    or changed so the caller can assert on it. Parts are removed WITH their [Content_Types] overrides and every
    relationship that points at them (removing parts alone corrupts the file in PowerPoint)."""
    entries = _read_zip(path)
    removed_parts = [i.filename for i, _ in entries if _is_removed(i.filename)]
    thumb_existed = any(i.filename == THUMB for i, _ in entries)
    if thumb_existed:
        removed_parts.append(THUMB)
    rep = {"parts_removed": sorted(removed_parts), "content_type_overrides_removed": [], "rels_removed": [],
           "core": {}, "app": {}, "thumbnail": None, "embedded_names_redacted": {}}
    out = []
    names = {i.filename for i, _ in entries}
    for info, data in entries:
        n = info.filename
        if n in removed_parts:
            continue
        if n == "[Content_Types].xml":
            t = data.decode("utf-8")
            for part in removed_parts:
                pat = re.compile(r'<Override[^>]*PartName="/%s"[^>]*/>' % re.escape(part))
                t, k = pat.subn("", t)
                if k:
                    rep["content_type_overrides_removed"].append(part)
            data = t.encode("utf-8")
        elif n.endswith(".rels"):
            t = data.decode("utf-8")
            base = posixpath.dirname(posixpath.dirname(n))     # folder the rels file describes
            def drop(m):
                tgt = re.search(r'Target="([^"]+)"', m.group(0))
                if tgt and 'TargetMode="External"' not in m.group(0):
                    full = posixpath.normpath(posixpath.join(base, tgt.group(1))) if not tgt.group(1).startswith("/") else tgt.group(1)[1:]
                    if full in removed_parts:
                        rep["rels_removed"].append((n, full))
                        return ""
                return m.group(0)
            t = re.sub(r"<Relationship\b[^>]*/>", drop, t)
            data = t.encode("utf-8")
        elif n == "docProps/core.xml":
            t = data.decode("utf-8")
            before = re.search(r"<cp:lastModifiedBy>([^<]*)<", t)
            t = re.sub(r"<cp:lastModifiedBy>[^<]*</cp:lastModifiedBy>", f"<cp:lastModifiedBy>{last_modified_by}</cp:lastModifiedBy>", t)
            t = re.sub(r"<dc:creator>[^<]*</dc:creator>", f"<dc:creator>{author}</dc:creator>", t)
            # The template's own title and dates must not survive into a deck that is not the template (12 Oct 2026).
            import datetime as _dt
            _now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _tm = re.search(r"<dc:title>([^<]*)</dc:title>", t)
            if title is not None:
                t = re.sub(r"<dc:title>[^<]*</dc:title>", f"<dc:title>{title}</dc:title>", t) if _tm else t.replace("</cp:coreProperties>", f"<dc:title>{title}</dc:title></cp:coreProperties>")
            elif _tm and _tm.group(1) == TEMPLATE_CORE["title"]:
                t = re.sub(r"<dc:title>[^<]*</dc:title>", "<dc:title></dc:title>", t)
            for _tag, _key in (("created", "created"), ("modified", "modified")):
                t = re.sub(rf'(<dcterms:{_tag}[^>]*>){re.escape(TEMPLATE_CORE[_key])}(</dcterms:{_tag}>)', rf"\g<1>{_now}\g<2>", t)
            rep["core"]["title"] = title if title is not None else ("blanked" if (_tm and _tm.group(1) == TEMPLATE_CORE["title"]) else (_tm.group(1) if _tm else None))
            rep["core"].update({"lastModifiedBy": (before.group(1) if before else None, last_modified_by), "creator": author})
            data = t.encode("utf-8")
        elif n == "docProps/app.xml":
            t = data.decode("utf-8")
            t = re.sub(r"<HeadingPairs>.*?</HeadingPairs>", "", t, flags=re.S)
            t = re.sub(r"<TitlesOfParts>.*?</TitlesOfParts>", "", t, flags=re.S)
            t = re.sub(r"<MMClips>\d+</MMClips>", "", t)
            slides = notes = words = paras = None
            try:
                prs = Presentation(path)
                slides = len(prs.slides)
                notes = sum(1 for sl in prs.slides if sl.has_notes_slide)
                texts = [p.text for sl in prs.slides for sh in sl.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs]
                paras = sum(1 for x in texts if x.strip())
                words = sum(len(x.split()) for x in texts)
            except Exception:
                pass
            if slide_count is not None:
                slides = slide_count
            for tag, val in (("Slides", slides), ("Notes", notes), ("Words", words), ("Paragraphs", paras)):
                if val is not None:
                    if re.search(rf"<{tag}>\d+</{tag}>", t):
                        t = re.sub(rf"<{tag}>\d+</{tag}>", f"<{tag}>{val}</{tag}>", t)
                    rep["app"][tag] = val
            data = t.encode("utf-8")
        if not n.endswith((".xml", ".rels")):
            data, k = redact_embedded(data)
            if k:
                rep["embedded_names_redacted"][n] = k
        out.append((info, data))
    if thumbnail_png:
        from PIL import Image
        im = Image.open(thumbnail_png).convert("RGB")
        im.thumbnail((256, 256))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
        out = [(i, d) for i, d in out if i.filename != THUMB]
        zi = zipfile.ZipInfo(THUMB, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
        out.append((zi, buf.getvalue()))
        fixed = []
        for info, data in out:
            if info.filename == "[Content_Types].xml":
                t = data.decode("utf-8")
                if not re.search(r'<Default[^>]*Extension="jpeg"', t, re.I):
                    t = t.replace("<Default ", '<Default Extension="jpeg" ContentType="image/jpeg"/><Default ', 1)
                data = t.encode("utf-8")
            elif info.filename == "_rels/.rels":
                t = data.decode("utf-8")
                if THUMB_REL not in t:
                    t = t.replace("</Relationships>", f'<Relationship Id="rIdThumb" Type="{THUMB_REL}" Target="{THUMB}"/></Relationships>')
                data = t.encode("utf-8")
            fixed.append((info, data))
        out = fixed
        rep["thumbnail"] = f"replaced from {Path(thumbnail_png).name} ({len(buf.getvalue())} bytes)"
    else:
        rep["thumbnail"] = "removed" if thumb_existed else "none"
        if thumb_existed:   # the thumbnail relationship in _rels/.rels was dropped by the generic rels pass
            pass
    tmp = Path(str(path) + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        out.sort(key=lambda x: x[0].filename != "[Content_Types].xml")
        for info, data in out:
            z.writestr(info.filename, data)
    tmp.replace(path)
    return rep


def main():
    parser = argparse.ArgumentParser(description="Build a deck on a brand template")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE),
                        help="Template .pptx to build on")
    parser.add_argument("--inspect", action="store_true",
                        help="List layouts and placeholders, then exit")
    parser.add_argument("--spec", help="JSON content spec (list of slides)")
    parser.add_argument("--out", help="Output .pptx path")
    parser.add_argument("--keep-samples", action="store_true",
                        help="Keep the template's original sample slides")
    args = parser.parse_args()

    tpl = Path(args.template)
    if not tpl.exists():
        sys.exit(f"Template not found: {tpl}")
    prs = Presentation(str(tpl))

    if args.inspect:
        inspect(prs)
        return

    if not args.spec or not args.out:
        parser.error("--spec and --out are required unless --inspect is given")

    if not args.keep_samples:
        drop_slides(prs)

    spec = json.loads(Path(args.spec).read_text())
    for slide_spec in spec:
        layout = find_layout(prs, slide_spec["layout"])
        slide = prs.slides.add_slide(layout)
        fill_slide(slide, slide_spec)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    rep = sanitise_package(out_path, slide_count=len(spec))
    findings, parts, text_parts = audit_package(out_path, deny_names=harvest_names(tpl))
    print(f"redacted embedded names in {len(rep['embedded_names_redacted'])} binary parts; ", end="")
    print(f"Saved {out_path} ({len(spec)} slides on {tpl.name}); sanitised {len(rep['parts_removed'])} parts; "
          f"audit: {len(findings)} findings over {parts} parts ({text_parts} text parts)")
    if findings:
        sys.exit(f"PACKAGE AUDIT FAILED: {len(findings)} findings, first: {findings[:3]}")


if __name__ == "__main__":
    main()
