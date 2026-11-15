#!/usr/bin/env python3
"""Enrich corpus_manifest.json's stock list with the app's own deterministic
system-of-record fields (price, days in stock, PDI status, recon status).
This is the app's OWN domain data (not ARAG-derived) - the structured half of
a DMS, deliberately separate from the unstructured KB content per the split
documented in the old build. Never uploaded to the KB.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(ROOT, "corpus_manifest.json")
with open(path) as f:
    manifest = json.load(f)

# stock_no -> (price AUD, days_in_stock, pdi_status, recon_status, blocker)
DATA = {
    "CM-5102": (42990, 6, "In recon", "Brake pads on order (BR-2210)", "Front brake pads below 3mm threshold"),
    "CM-5118": (48990, 11, "PDI hold", "Recall remedy scheduled", "Open recall - rear differential seal, remedy not yet applied"),
    "CM-5124": (46490, 4, "In recon", "Infotainment update pending", "Software update required before delivery"),
    "CM-5137": (24990, 19, "Ready for delivery", "Tensioner replacement complete", None),
    "CM-5145": (58990, 3, "Ready for delivery", "DPF regeneration complete", None),
    "CM-5150": (36990, 8, "PDI hold", "Firmware remedy applied, awaiting re-verification", "Open recall - airbag control unit, remedy applied, PDI re-check pending"),
    "CM-5163": (13990, 2, "Ready for delivery", "Standard detail only", None),
    "CM-5171": (28990, 24, "Ready for delivery", "Disclosure prepared - prior repaint", None),
    "CM-5184": (54990, 9, "PDI hold", "Recall remedy applied, road test logged", "Open recall - fuel pump control module, awaiting final sign-off"),
    "CM-5192": (39990, 14, "Ready for delivery", "ADAS recalibration passed (2nd attempt)", None),
    "CM-5205": (21990, 5, "Ready for delivery", "Standard detail only", None),
    "CM-5213": (44990, 21, "Ready for delivery", "Preventative seal replacement complete", None),
    "CM-5226": (16990, 1, "Ready for delivery", "Standard detail only", None),
    "CM-5234": (37990, 17, "In recon", "Alignment correction before tyre fitment", "Rear alignment out of spec - correct before fitting new tyres"),
}

for s in manifest["stock"]:
    price, days, pdi, recon, blocker = DATA[s["no"]]
    s["price"] = price
    s["days_in_stock"] = days
    s["pdi_status"] = pdi
    s["recon_status"] = recon
    s["blocker"] = blocker

with open(path, "w") as f:
    json.dump(manifest, f, indent=2)

print("Enriched", len(manifest["stock"]), "stock records.")
