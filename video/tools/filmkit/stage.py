#!/usr/bin/env python3
"""Mount a film composition, seek its paused timeline, and read what renders.

THE ONE PRIMITIVE. Every pre-render check in this kit is a function over a
mounted composition, because every pre-render check needs the same three things:
the composition's own timeline, the DOM after layout, and the pixels.

Why this exists as shared code rather than per film: fin-demo-showcase wrote 24
tools_*.py in one evening, videos/kuraray-portal five more, and
videos/sa-use-cases/checks holds a COPY of scripts/frame_measures.py rather than
an import. Thirteen of those 24 are pre-render instruments, which means the
instruments that catch a defect before a render exist, and exist in exactly one
project. A defect class caught on one film does not currently protect the next.

Measurement contract, and each clause is a defect this factory has shipped:

* device_scale_factor is 1, so a CSS pixel is a rendered pixel. A measurement
  taken at 2 reports half the glyph.
* Geometry comes from getBoundingClientRect AFTER layout and AFTER every
  transform. Compositions here translate #root's children (frame 05 drops the
  whole layer stack 41px), so an authored coordinate is not a rendered one.
* A failed asset request is FATAL, never a warning. A frame missing its images
  is not the frame that ships, and it measures as cleaner than it is.
* Text geometry is read from leaf elements only. A parent's rect is the union of
  its children and tells you nothing about a glyph.
* Every reader returns its POPULATION COUNT beside its result, because zero of
  zero is not a pass.

Blind classes, declared here so a clean result from this stage is not mistaken
for a clean frame:

* It cannot see anything the RENDERER does that the browser does not - encode,
  colour conversion, scaling to the delivery container.
* It reads a composition in isolation, so it cannot see a cross-dissolve from a
  neighbouring shot covering or revealing anything.
* A callback-driven change does not re-run on a SEEK (GSAP replays tweens and
  tl.set, never tl.add(fn)), so anything a composition does in a callback is
  invisible here and visible in the render. That asymmetry is itself a defect
  under the kit's own rules - see checks/beats.py.
* Text inside a captured plate is pixels, not DOM. checks/platetext.py reads it
  by OCR; this stage will not.

Concurrency: every instance gets a private temp directory, so any number of
checks or agents may run against one project at once. Nothing is written into
the project tree.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import tempfile
import urllib.request
from dataclasses import dataclass, field

GSAP_URL = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
# Cached outside the repo: scripts/ is version-controlled under hard rule 16 and
# a vendored library is a run output, not configuration. Same reasoning as the
# OCR cache in plate.py.
GSAP_CACHE = pathlib.Path(tempfile.gettempdir()) / "filmkit-gsap-3.14.2.js"

# 1920-wide frame shown at 390 CSS px. The unit the verdict is made in is the
# delivery medium, never the authored pixel.
PHONE_CSS_WIDTH = 390


def gsap_source() -> str:
    if not GSAP_CACHE.exists():
        urllib.request.urlretrieve(GSAP_URL, GSAP_CACHE)
    return GSAP_CACHE.read_text()


@dataclass
class Composition:
    path: pathlib.Path
    cid: str
    declared_duration: float | None
    body: str

    @property
    def name(self) -> str:
        return self.path.name


@dataclass
class TextBox:
    text: str
    x: float
    y: float
    w: float
    h: float
    font_size: float          # computed, CSS px, after transforms
    rendered_font_size: float  # font_size * cumulative transform scale
    line_height: float
    colour: str
    selector: str
    opacity: float
    t: float                   # the timeline position this was read at

    def at_delivery(self, frame_width: int, css_width: int = PHONE_CSS_WIDTH) -> float:
        """Glyph height in CSS px on the delivery medium."""
        return self.rendered_font_size * (css_width / frame_width)


@dataclass
class ImageBox:
    src: str
    natural_w: int
    natural_h: int
    x: float
    y: float
    w: float
    h: float
    selector: str
    t: float

    @property
    def upscale(self) -> float:
        """>1 means the source is being enlarged, which is always visible as soft."""
        if not self.natural_w or not self.w:
            return 0.0
        return self.w / self.natural_w


class StageError(RuntimeError):
    pass


class FilmStage:
    """One browser, many compositions. Use as a context manager."""

    def __init__(
        self,
        project_root: str | pathlib.Path,
        frames_glob: str = "compositions/frames/*.html",
        width: int = 1920,
        height: int = 1080,
        stage_bg: str = "#00216B",
    ):
        self.root = pathlib.Path(project_root).resolve()
        if not self.root.is_dir():
            raise StageError(f"project root does not exist: {self.root}")
        self.frames_glob = frames_glob
        self.width = width
        self.height = height
        self.stage_bg = stage_bg
        self._pw = None
        self._browser = None
        self._page = None
        self._harness: pathlib.Path | None = None
        self._tmpdir: pathlib.Path | None = None
        self._failed: list[str] = []
        self._mounted: Composition | None = None

    # -- lifecycle ---------------------------------------------------------

    def __enter__(self) -> "FilmStage":
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch()
        self._page = self._browser.new_page(
            viewport={"width": self.width, "height": self.height},
            device_scale_factor=1,
        )
        self._page.on("requestfailed", lambda r: self._failed.append(r.url.rsplit("/", 1)[-1]))
        harness = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
            f"html,body{{margin:0;width:{self.width}px;height:{self.height}px;"
            f"overflow:hidden;background:{self.stage_bg}}}</style>"
            "<script>" + gsap_source() + "</script></head>"
            "<body><div id='mount'></div></body></html>"
        )
        # PRIVATE per-instance directory, never a fixed name in the project.
        # The first version wrote ._filmkit_harness.html into the project root,
        # and four agents running this stage against one project deleted each
        # other's harness on exit - ERR_FILE_NOT_FOUND mid-run, non-deterministic,
        # and nothing in any caller was wrong. The discharge for shared mutable
        # state is isolation, not a convention about who cleans up. The base href
        # set in mount() is what resolves the project's own assets, so the harness
        # itself does not need to live beside them.
        self._tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="filmkit-stage-"))
        self._harness = self._tmpdir / "harness.html"
        self._harness.write_text(harness)
        return self

    def __exit__(self, *exc) -> None:
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        if getattr(self, "_tmpdir", None):
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    # -- discovery ---------------------------------------------------------

    def compositions(self) -> list[Composition]:
        found = sorted(self.root.glob(self.frames_glob))
        if not found:
            raise StageError(
                f"no compositions matched {self.frames_glob!r} under {self.root} - "
                "a sweep over an empty population is not a pass"
            )
        out = []
        for f in found:
            src = f.read_text()
            m = re.search(r"<template[^>]*>(.*)</template>", src, re.S)
            inner = m.group(1) if m else src
            head = src[: src.find(">") + 1] if m else src[:400]
            body = re.sub(r'<script src="[^"]*gsap[^"]*"></script>', "", inner)
            cid_m = re.search(r'data-composition-id="([^"]+)"', src)
            if not cid_m:
                raise StageError(f"{f.name}: no data-composition-id - cannot resolve its timeline")
            dur_m = re.search(r'data-duration="([0-9.]+)"', head) or re.search(
                r'data-duration="([0-9.]+)"', src
            )
            out.append(
                Composition(
                    path=f,
                    cid=cid_m.group(1),
                    declared_duration=float(dur_m.group(1)) if dur_m else None,
                    body=body,
                )
            )
        return out

    # -- mount and seek ----------------------------------------------------

    def mount(self, comp: Composition, settle_ms: int = 1200) -> None:
        self._failed.clear()
        pg = self._page
        pg.goto(self._harness.as_uri())
        pg.evaluate(
            """({body, base}) => {
                window.__timelines = {};
                const b = document.createElement('base');
                b.href = base;
                document.head.appendChild(b);
                document.getElementById('mount').innerHTML = body;
                document.querySelectorAll('#mount script').forEach(s => {
                    const n = document.createElement('script');
                    n.textContent = s.textContent;
                    document.body.appendChild(n);
                });
            }""",
            {"body": comp.body, "base": self.root.as_uri() + "/"},
        )
        # Wait for the two things that actually have to be true - fonts resolved
        # and the timeline registered - rather than sleeping a fixed 1200ms.
        # Measured: a fixed settle cost 14.7s per pass of 12 compositions, and
        # four checks each mounting the whole film made that 59s of a 138s gate
        # run. settle_ms is now a CEILING, not a duration.
        deadline = settle_ms
        waited = 0
        while waited < deadline:
            ready = pg.evaluate(
                """(cid) => (document.fonts ? document.fonts.status === 'loaded' : true)
                            && !!(window.__timelines && window.__timelines[cid])""",
                comp.cid,
            )
            if ready:
                break
            pg.wait_for_timeout(40)
            waited += 40
        pg.wait_for_timeout(40)        # one frame for layout to settle after fonts
        registered = pg.evaluate(
            "(cid) => !!(window.__timelines && window.__timelines[cid])", comp.cid
        )
        if not registered:
            raise StageError(
                f"{comp.name}: no timeline registered for {comp.cid!r}. "
                "Every reading below would have described a static first frame."
            )
        if self._failed:
            raise StageError(
                f"{comp.name}: {len(self._failed)} asset(s) failed to load "
                f"{sorted(set(self._failed))[:6]} - a frame missing its images is not the "
                "frame that ships, and it measures cleaner than it is"
            )
        self._mounted = comp

    def duration(self) -> float:
        return float(
            self._page.evaluate(
                "(cid) => window.__timelines[cid].duration()", self._mounted.cid
            )
        )

    def seek(self, t: float, settle_ms: int = 120) -> None:
        self._page.evaluate(
            """({cid, t}) => { window.__timelines[cid].seek(t, false); }""",
            {"cid": self._mounted.cid, "t": float(t)},
        )
        if settle_ms:
            self._page.wait_for_timeout(settle_ms)

    def screenshot(self, out: str | pathlib.Path) -> pathlib.Path:
        out = pathlib.Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(out))
        return out

    def evaluate(self, js: str, arg=None):
        return self._page.evaluate(js, arg)

    # -- readers -----------------------------------------------------------

    _TEXT_JS = """(t) => {
        const out = [], root = document.getElementById('mount');
        const sel = (el) => {
            if (el.id) return '#' + el.id;
            const c = (el.className || '').toString().trim().split(/\\s+/).filter(Boolean);
            return el.tagName.toLowerCase() + (c.length ? '.' + c[0] : '');
        };
        // cumulative scale from every ancestor transform
        const scaleOf = (el) => {
            let s = 1, n = el;
            while (n && n !== document.body) {
                const m = new DOMMatrixReadOnly(getComputedStyle(n).transform);
                if (m.a) s *= Math.abs(m.a);
                n = n.parentElement;
            }
            return s;
        };
        const opacityOf = (el) => {
            let o = 1, n = el;
            while (n && n !== document.body) {
                const v = parseFloat(getComputedStyle(n).opacity);
                if (!isNaN(v)) o *= v;
                n = n.parentElement;
            }
            return o;
        };
        root.querySelectorAll('*').forEach(el => {
            if (el.children.length) return;                 // leaves only
            const txt = (el.innerText || el.textContent || '').trim();
            if (!txt) return;
            const cs = getComputedStyle(el);
            if (cs.visibility === 'hidden' || cs.display === 'none') return;
            const op = opacityOf(el);
            if (op <= 0.01) return;
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return;
            const fs = parseFloat(cs.fontSize) || 0;
            const lh = parseFloat(cs.lineHeight) || fs;
            const sc = scaleOf(el);
            out.push({text: txt, x: r.x, y: r.y, w: r.width, h: r.height,
                      font_size: fs, rendered_font_size: fs * sc, line_height: lh,
                      colour: cs.color, selector: sel(el), opacity: op, t: t});
        });
        return out;
    }"""

    def text_boxes(self, t: float | None = None) -> list[TextBox]:
        """Every leaf text element visible at the current (or given) timeline point."""
        if t is not None:
            self.seek(t)
        at = t if t is not None else -1.0
        rows = self._page.evaluate(self._TEXT_JS, at)
        return [TextBox(**r) for r in rows]

    _IMG_JS = """(t) => {
        const out = [], root = document.getElementById('mount');
        const sel = (el) => {
            if (el.id) return '#' + el.id;
            const c = (el.className || '').toString().trim().split(/\\s+/).filter(Boolean);
            return el.tagName.toLowerCase() + (c.length ? '.' + c[0] : '');
        };
        root.querySelectorAll('img').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return;
            const cs = getComputedStyle(el);
            if (cs.visibility === 'hidden' || cs.display === 'none') return;
            out.push({src: el.currentSrc || el.src, natural_w: el.naturalWidth,
                      natural_h: el.naturalHeight, x: r.x, y: r.y, w: r.width,
                      h: r.height, selector: sel(el), t: t});
        });
        root.querySelectorAll('*').forEach(el => {
            const bg = getComputedStyle(el).backgroundImage;
            if (!bg || bg === 'none' || !bg.includes('url(')) return;
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return;
            const url = bg.slice(bg.indexOf('url(') + 4).replace(/^["']|["']\\)?.*$/g, '');
            out.push({src: url, natural_w: 0, natural_h: 0, x: r.x, y: r.y,
                      w: r.width, h: r.height, selector: sel(el), t: t});
        });
        return out;
    }"""

    def image_boxes(self, t: float | None = None) -> list[ImageBox]:
        """Every <img> and background-image, with natural vs displayed size.

        natural_w is 0 for a CSS background-image: the browser does not expose it.
        checks/capturefidelity.py resolves those off disk rather than guessing,
        and says which ones it could not resolve.
        """
        if t is not None:
            self.seek(t)
        at = t if t is not None else -1.0
        return [ImageBox(**r) for r in self._page.evaluate(self._IMG_JS, at)]

    def visible_strings(self, steps: int = 60) -> list[str]:
        """Union of rendered innerText across the whole timeline.

        Source is the wrong population for a copy rule: a sweep over source
        returns CSS property names and comment text, and misses copy a script
        injects at t=9s. This walks the timeline instead.
        """
        return self._page.evaluate(
            """({cid, steps}) => {
                const tl = window.__timelines[cid], D = tl.duration();
                const seen = new Set(), root = document.getElementById('mount');
                for (let i = 0; i <= steps; i++) {
                    tl.seek(D * i / steps, false);
                    root.querySelectorAll('*').forEach(el => {
                        if (el.children.length) return;
                        const t = (el.innerText || el.textContent || '').trim();
                        if (!t) return;
                        const cs = getComputedStyle(el);
                        if (cs.visibility === 'hidden' || cs.display === 'none') return;
                        seen.add(t);
                    });
                }
                return [...seen];
            }""",
            {"cid": self._mounted.cid, "steps": steps},
        )

    def beats(self) -> list[dict]:
        """The REGISTERED timeline, not the authored source.

        A retime that edits source literals is verified by comparing what the
        timeline registers before and after. An un-wrapped literal keeps its old
        value and the diff looks applied.
        """
        return self._page.evaluate(
            """(cid) => window.__timelines[cid].getChildren(true, true, true).map(c => ({
                 start: c.startTime(), dur: c.duration(),
                 targets: (c.targets ? c.targets() : []).map(
                     el => el && el.id ? '#' + el.id :
                           (el && el.className ? el.tagName.toLowerCase() + '.' +
                            (el.className||'').toString().trim().split(/\\s+/)[0] : String(el))),
                 kind: c.constructor.name
               }))""",
            self._mounted.cid,
        )

    def callback_beats(self) -> int:
        """How many timeline children are bare callbacks.

        A callback does not re-run when a PAUSED timeline is seeked, so anything
        it changes is alive in the render and dead in every frame this stage
        reads - and dead in HyperFrames, which renders by seeking. Non-zero here
        is a finding about the composition, not about the stage.
        """
        return self._page.evaluate(
            """(cid) => window.__timelines[cid].getChildren(true, true, true)
                 .filter(c => c.vars && typeof c.vars.onComplete === 'function'
                              && !(c.targets && c.targets().length)).length""",
            self._mounted.cid,
        )
