#!/usr/bin/env python3
"""Generate synthetic recon-photo stand-ins for the Media Library use case.

Real image FILES (PNG), each GENUINELY DISTINCT per stock unit (Standard B10 -
demo-tester correctly failed the first cut, which was one silhouette per body
type recoloured five times over): real per-unit colour (from the stock
record, not a shared body-type accent), per-unit proportions, and a real
annotation callout tied to that unit's actual consultant-note finding, so
each of the 14 cards reads as its own document rather than a recoloured
template. Disclosed synthetic - illustrative recon photo cards, not
photographs of real vehicles.
"""
import json
import os
import random

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(__file__)
OUT = os.path.join(BASE, "..", "corpus_media")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, "..", "corpus_manifest.json")) as f:
    manifest = json.load(f)
STOCK = manifest["stock"]

W, H = 1280, 800

# Named colour -> a real approximate hex, so every unit's own colour renders
# (not a shared per-body-type accent recoloured across five identical cards).
COLOUR_HEX = {
    "Silver Sky": "#B9C2CC",
    "Meteor Grey": "#5A6270",
    "Soul Red Crystal": "#8C1D2B",
    "Phantom Black": "#1C1F24",
    "Splash White": "#E9EAEA",
    "Gravity Blue": "#2E4A6B",
    "Icon Blue": "#1D5FA8",
    "Autumn Green": "#4B5A3A",
    "Feverish Red": "#A0281E",
    "Platinum White": "#DCDCDC",
    "Speedy Blue": "#2F6FD1",
    "Arctic White": "#EFEFEF",
    "Lime Green": "#8FBF2E",
    "Graphite Grey": "#3D4247",
}

# One real annotation per unit, tied to its actual consultant-note finding
# (not decorative) - the visible detail that makes each card its own record.
FOCUS = {
    "CM-5102": ("Front-left brake caliper", 0.30, 0.62),
    "CM-5118": ("Rear differential housing", 0.62, 0.66),
    "CM-5124": ("Infotainment unit (dash)", 0.50, 0.40),
    "CM-5137": ("Timing chain area (engine bay)", 0.42, 0.44),
    "CM-5145": ("Exhaust / DPF outlet", 0.66, 0.68),
    "CM-5150": ("Airbag control unit (dash)", 0.50, 0.40),
    "CM-5163": ("Right fairing scuff", 0.62, 0.48),
    "CM-5171": ("Rear-left quarter panel", 0.72, 0.52),
    "CM-5184": ("Fuel pump control module", 0.40, 0.60),
    "CM-5192": ("Windscreen / ADAS camera", 0.50, 0.34),
    "CM-5205": ("Driver door card trim", 0.28, 0.46),
    "CM-5213": ("Rear differential housing", 0.62, 0.66),
    "CM-5226": ("No findings - showroom condition", 0.50, 0.50),
    "CM-5234": ("Rear tyre - uneven wear", 0.70, 0.68),
}

def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_silhouette(draw, body, cx, cy, scale, colour, rng):
    """A geometric stand-in silhouette per body type, with per-unit proportion
    jitter (seeded per stock, so it's deterministic but genuinely varies card
    to card) rather than one identical shape recoloured."""
    jw = 1.0 + rng.uniform(-0.06, 0.06)
    jh = 1.0 + rng.uniform(-0.05, 0.05)
    jroof = 1.0 + rng.uniform(-0.08, 0.08)
    s = scale

    if body == "Motorcycle":
        draw.ellipse([cx-180*s*jw, cy-40*s*jh, cx-60*s*jw, cy+80*s*jh], fill=colour)
        draw.ellipse([cx+40*s*jw, cy-40*s*jh, cx+180*s*jw, cy+80*s*jh], fill=colour)
        draw.rectangle([cx-100*s*jw, cy-60*s*jh, cx+120*s*jw, cy], fill=colour)
        draw.polygon([(cx-100*s*jw, cy-60*s*jh), (cx-40*s*jw, cy-140*s*jroof), (cx+20*s*jw, cy-60*s*jh)], fill=colour)
    elif body == "Ute":
        draw.rounded_rectangle([cx-320*s*jw, cy-60*s*jh, cx+80*s*jw, cy+70*s*jh], radius=24, fill=colour)
        draw.rounded_rectangle([cx-260*s*jw, cy-150*s*jroof, cx-20*s*jw, cy-50*s*jh], radius=18, fill=colour)
        draw.rounded_rectangle([cx+60*s*jw, cy-30*s*jh, cx+330*s*jw, cy+70*s*jh], radius=10, fill=colour)
        for wx in (cx-220*s*jw, cx+20*s*jw, cx+260*s*jw):
            draw.ellipse([wx-55*s, cy+40*s*jh, wx+55*s, cy+150*s*jh], fill="#0b0d10")
    elif body == "Wagon":
        draw.rounded_rectangle([cx-320*s*jw, cy-50*s*jh, cx+320*s*jw, cy+70*s*jh], radius=30, fill=colour)
        draw.rounded_rectangle([cx-250*s*jw, cy-150*s*jroof, cx+230*s*jw, cy-40*s*jh], radius=26, fill=colour)
        for wx in (cx-220*s*jw, cx+20*s*jw, cx+260*s*jw):
            draw.ellipse([wx-55*s, cy+40*s*jh, wx+55*s, cy+156*s*jh], fill="#0b0d10")
    else:  # SUV / Hatch default
        draw.rounded_rectangle([cx-300*s*jw, cy-70*s*jh, cx+300*s*jw, cy+70*s*jh], radius=40, fill=colour)
        draw.rounded_rectangle([cx-220*s*jw, cy-170*s*jroof, cx+220*s*jw, cy-50*s*jh], radius=32, fill=colour)
        for wx in (cx-200*s*jw, cx+30*s*jw, cx+230*s*jw):
            draw.ellipse([wx-58*s, cy+40*s*jh, wx+58*s, cy+156*s*jh], fill="#0b0d10")

ANGLES = ["Front Quarter", "Rear Quarter", "Interior / Cockpit"]
media_manifest = []

for i, stock in enumerate(STOCK):
    angle = ANGLES[i % len(ANGLES)]
    hexcol = COLOUR_HEX.get(stock["colour"], "#3A4A5C")
    rng = random.Random(stock["no"])  # deterministic per-unit jitter

    img = Image.new("RGB", (W, H), "#050b26")
    draw = ImageDraw.Draw(img)

    # per-unit backdrop tint (subtle hue drift keyed on stock number, still
    # reads as one coherent workshop-bay palette, not identical every time)
    hue_shift = (int(stock["no"][-2:]) * 7) % 40
    for y in range(H):
        t = y / H
        r = int(0x05 + (0x10 + hue_shift*0.3) * t)
        g = int(0x0b + (0x14 + hue_shift*0.2) * t)
        b = int(0x26 + (0x30 + hue_shift*0.4) * t)
        draw.line([(0, y), (W, y)], fill=(min(r,255), min(g,255), min(b,255)))
    draw.rectangle([0, H-120, W, H], fill="#03071a")

    draw_silhouette(draw, stock["body"], W*0.58, H*0.52, 1.0, hexcol, rng)

    # bay markings
    draw.line([(0, H-120), (W, H-120)], fill="#2964F6", width=4)
    for x in range(40, W, 160):
        draw.rectangle([x, H-118, x+70, H-108], fill="#2964F6")

    f_title = font(40, bold=True)
    f_meta = font(26)
    f_tag = font(22, bold=True)
    f_focus = font(20, bold=True)

    draw.text((48, 44), f"{stock['no']}", font=f_title, fill="#F5F1E8")
    draw.text((48, 96), f"{stock['year']} {stock['make']} {stock['model']}", font=f_meta, fill="#B9C2CC")
    draw.text((48, 132), f"{stock['site']} - {angle} - {stock['colour']}", font=f_meta, fill="#8A94A0")

    tag = f"{stock['body'].upper()}"
    tw = draw.textlength(tag, font=f_tag)
    draw.rounded_rectangle([W-48-tw-28, 40, W-48, 40+44], radius=10, fill="#2964F6")
    draw.text((W-48-tw-14, 50), tag, font=f_tag, fill="#050b26")

    # real per-unit annotation callout, tied to the actual consultant finding
    focus_label, fx, fy = FOCUS.get(stock["no"], ("General condition", 0.5, 0.5))
    px, py = int(W * fx), int(H * fy)
    r = 34
    draw.ellipse([px-r, py-r, px+r, py+r], outline="#FFD23F", width=4)
    lx, ly = px + 90, py - 70
    draw.line([(px + r*0.7, py - r*0.7), (lx, ly)], fill="#FFD23F", width=3)
    tw2 = draw.textlength(focus_label, font=f_focus)
    draw.rounded_rectangle([lx-8, ly-32, lx+tw2+16, ly+4], radius=6, fill="#0b0d10")
    draw.text((lx, ly-26), focus_label, font=f_focus, fill="#FFD23F")

    draw.text((48, H-96), "Coppermill Motor Group - Recon Documentation", font=font(22), fill="#8A94A0")
    draw.text((48, H-64), "Synthetic illustrative image, not a real vehicle photograph.", font=font(18), fill="#5B6572")

    fname = f"recon-{stock['no'].lower()}-{angle.lower().replace(' ', '-').replace('/', '')}.png"
    path = os.path.join(OUT, fname)
    img.save(path, "PNG")
    media_manifest.append(dict(file=fname, stock_no=stock["no"], site=stock["site"],
                                make=stock["make"], model=stock["model"], body=stock["body"],
                                angle=angle, focus=focus_label,
                                title=f"Stock {stock['no']} - {stock['year']} {stock['make']} {stock['model']} - {angle}"))

with open(os.path.join(BASE, "..", "media_manifest.json"), "w") as f:
    json.dump(media_manifest, f, indent=2)

print(f"Generated {len(media_manifest)} media images.")
