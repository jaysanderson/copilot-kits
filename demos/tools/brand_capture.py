"""Capture brand assets (screenshot, logo, palette, fonts) for a customer domain.

Usage:
    python scripts/brand_capture.py tangerinetelecom.com.au
"""
import colorsys
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image
from playwright.sync_api import sync_playwright

# Outputs land under the current working directory (the project root), so the
# script is portable across projects when bundled in a skill.
BRAND_DIR = Path("brand")

# Match browser UA so servers hand back the real homepage, not a bot page.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)


def near_white(rgb, threshold=240):
    return all(c >= threshold for c in rgb)


def near_black(rgb, threshold=20):
    return all(c <= threshold for c in rgb)


def _hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def extract_palette(image_path, count=5):
    """Return (palette, primary).

    `palette` is the `count` most frequent colours (skipping near-white/black).
    `primary` is the brand colour chosen by frequency * saturation, so a vivid
    accent (e.g. Tangerine orange) wins over a large pale background block that
    would otherwise dominate a purely frequency-ranked palette.
    """
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((400, 400))
    quantized = img.quantize(colors=64, method=Image.Quantize.FASTOCTREE)
    palette = quantized.getpalette()  # flat [r,g,b, r,g,b, ...]

    ranked = []  # (freq, rgb)
    for freq, idx in sorted(quantized.getcolors(), reverse=True):
        rgb = tuple(palette[idx * 3 : idx * 3 + 3])
        if near_white(rgb) or near_black(rgb):
            continue
        ranked.append((freq, rgb))

    palette_hex = [_hex(rgb) for _, rgb in ranked[:count]]

    def sat(rgb):
        return colorsys.rgb_to_hsv(*[c / 255 for c in rgb])[1]

    # Weight frequency by saturation; ignore near-grey colours entirely.
    vivid = [(freq * sat(rgb) ** 2, rgb) for freq, rgb in ranked if sat(rgb) > 0.25]
    primary = _hex(max(vivid)[1]) if vivid else (palette_hex[0] if palette_hex else None)
    return palette_hex, primary


def download(url, dest_stem, session):
    """Download url to <dest_stem>.<ext-from-content-type-or-url>. Returns path or None.

    dest_stem is a full path prefix; the extension is appended (not substituted
    via with_suffix, which would mangle dotted domain names).
    """
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  logo download failed ({url}): {exc}", file=sys.stderr)
        return None

    content_type = resp.headers.get("content-type", "").split(";")[0].strip()
    ext_map = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/svg+xml": "svg",
        "image/gif": "gif",
        "image/webp": "webp",
        "image/x-icon": "ico",
        "image/vnd.microsoft.icon": "ico",
    }
    ext = ext_map.get(content_type)
    if not ext:
        ext = Path(urlparse(url).path).suffix.lstrip(".") or "png"
    dest = dest_stem.parent / f"{dest_stem.name}.{ext}"
    dest.write_bytes(resp.content)
    return dest


def find_logo_candidates(page, base_url):
    """Ordered logo candidates: og:image, first header/nav <img>, favicon."""
    candidates = []

    # 1. og:image
    og = page.query_selector('meta[property="og:image"]')
    if og:
        content = og.get_attribute("content")
        if content:
            candidates.append(urljoin(base_url, content))

    # 2. first <img> inside a header/nav element
    img = page.query_selector("header img, nav img")
    if img:
        src = img.get_attribute("src") or img.get_attribute("data-src")
        if src:
            candidates.append(urljoin(base_url, src))

    # 3. favicon
    icon = page.query_selector('link[rel~="icon"], link[rel="shortcut icon"]')
    if icon:
        href = icon.get_attribute("href")
        if href:
            candidates.append(urljoin(base_url, href))
    candidates.append(urljoin(base_url, "/favicon.ico"))

    # De-dupe while preserving order.
    seen = set()
    return [c for c in candidates if not (c in seen or seen.add(c))]


def main():
    if len(sys.argv) < 2:
        print("Usage: python brand_capture.py <domain> [kit-name]", file=sys.stderr)
        sys.exit(1)

    import re
    raw = sys.argv[1].strip()
    url = raw if raw.startswith("http") else f"https://{raw}"
    # A safe filename slug (handles full URLs with a path, e.g. site.com/event).
    bare = re.sub(r"^https?://", "", raw.lower())
    slug = re.sub(r"[^a-z0-9]+", "-", bare).strip("-")
    # Optional kit name writes brand/<kit>.json (a reusable brand kit); the
    # default "brand" matches the create-mode live-capture flow.
    kit = sys.argv[2] if len(sys.argv) > 2 else "brand"
    BRAND_DIR.mkdir(exist_ok=True)

    screenshot_path = BRAND_DIR / f"{slug}-home.png"
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1920, "height": 1080}, user_agent=USER_AGENT
        )
        page.goto(url, wait_until="load", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass  # best effort; some sites never go idle

        page.screenshot(path=str(screenshot_path), full_page=True)

        logo_candidates = find_logo_candidates(page, url)

        fonts = page.evaluate(
            """() => {
                const body = document.body;
                const h1 = document.querySelector('h1');
                const ff = (el) => el ? getComputedStyle(el).fontFamily : null;
                return { body: ff(body), heading: ff(h1) };
            }"""
        )
        browser.close()

    logo_path = None
    for candidate in logo_candidates:
        logo_path = download(candidate, BRAND_DIR / f"{slug}-logo", session)
        if logo_path:
            break

    palette, primary = extract_palette(screenshot_path)

    brand = {
        "domain": bare,
        "logo": logo_path.name if logo_path else None,
        "primary": primary,          # saturation-weighted brand colour
        "palette": palette,          # frequency-ranked dominant colours
        "fonts": fonts,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }

    brand_json = BRAND_DIR / f"{kit}.json"
    brand_json.write_text(json.dumps(brand, indent=2) + "\n")
    print(f"Wrote {brand_json}")
    print(json.dumps(brand, indent=2))


if __name__ == "__main__":
    main()
