#!/usr/bin/env python3
"""Extract frames from the delivered film for an eye-read, as tiles AND full size.

The instruments here measure emptiness, legibility, contrast and text. None of
them can see a frame that is populated, legible and WRONG, so the eye-read is a
gate step in its own right. Tiles are kept large (3 per sheet) because the
review medium must not be stricter than the delivery medium - a 560px tile
makes a 40px label look like 12px and invents a defect that is not there.
"""
import subprocess, sys, pathlib, json
from PIL import Image

P = pathlib.Path(__file__).parent
OUT = P / ".eyeread"


def main(film, per_shot=2):
    tl = json.load(open(P / "timeline.json"))
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.jpg"):
        f.unlink()
    names = ["01-powered-by", "02-sample-pack", "03-the-hard-page", "04-step-1-split",
             "05-step-2-identify", "06-step-3-ask", "07-step-4-score", "08-step-5-delete",
             "09-the-output", "10-measured", "11-messy-ones", "12-powered-by-close"]
    shots = []
    for i, n in enumerate(names):
        s, d = tl["scene_start"][i], tl["scene_dur"][i]
        # sample inside the scene, clear of both transitions
        for k in range(per_shot):
            t = s + 0.75 + (d - 1.6) * (k + 0.5) / per_shot
            shots.append((f"{i+1:02d}_{n}_{k}", t))
    for tag, t in shots:
        p = OUT / f"{tag}_{t:07.2f}.jpg"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}",
                        "-i", film, "-frames:v", "1", "-q:v", "2", str(p)], check=True)
    files = sorted(OUT.glob("*.jpg"))
    print(f"{len(files)} frames extracted to {OUT}")
    # contact sheets, 3 tiles each at 900px wide so type stays judgeable
    W = 900
    for s in range(0, len(files), 3):
        grp = files[s:s + 3]
        ims = [Image.open(f).resize((W, int(W * 1080 / 1920))) for f in grp]
        sheet = Image.new("RGB", (W, sum(im.height for im in ims)), "black")
        y = 0
        for im in ims:
            sheet.paste(im, (0, y)); y += im.height
        sheet.save(OUT / f"sheet_{s//3:02d}.png")
    print(f"{(len(files)+2)//3} contact sheets written")
    for f in files:
        print("  ", f.name)


if __name__ == "__main__":
    main(sys.argv[1])
