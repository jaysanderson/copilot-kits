# Progress deck kit

Recipes, builders, brand tokens and gates for building Progress-branded 16:9 decks on the corporate master template, packaged for GitHub Copilot in VS Code.

## What is here
- `.github/copilot-instructions.md`: always-on rules (under 50 lines). `.github/instructions/`: rules that load only for builder files. `.github/prompts/`: `/new-deck`, `/renovate-deck`, `/deck-gate`, `/brand-audit`.
- `builders/build_from_template.py`: fills a JSON spec onto the template and sanitises the package. `builders/anz-sales-meeting/`: a scripted deck with `checks.py`. `builders/build.py`, `deck-spec.json`, `sitefinity-connector-spec.json`: worked examples.
- `templates/progress-corporate-fy26.pptx`: the master (68 layouts). `templates/Corporate PPT Template Guide.pdf`: the brand team's guide.
- `brand/`: `progress-official.json` tokens, the real Progress logo in dark and white, Progress Sans files (video only, never embedded in a pptx), `LOGO-SLOTS-README.md`.
- `DEFINITION-OF-PASS.md`: the numbered bar every deck is gated against. `reference/`: the source skills and the full DoP, for reading, not for loading into every chat.

## Start a deck
1. Open Copilot Chat in agent mode and run `/new-deck` with the audience, purpose and source material. Approve the outline before anything is built.
2. Spec decks: Copilot writes `decks/<name>/<name>-spec.json` and runs `python builders/build_from_template.py --template templates/progress-corporate-fy26.pptx --spec decks/<name>/<name>-spec.json --out decks/<name>/<name>.pptx`.
3. Scripted decks: copy `builders/anz-sales-meeting/` to `decks/<name>/`, repoint `ROOT`, `TEMPLATE`, `OUT` and the Arial font path (they are Mac paths from the source project), replace the `deck_design` import with helpers from `builders/build.py`, then edit `body.py` and `checks.py`.
4. Render: `soffice --headless --convert-to pdf --outdir decks/<name>/qa decks/<name>/<name>.pptx` then `pdftoppm -jpeg -r 150 decks/<name>/qa/<name>.pdf decks/<name>/qa/slide`. Look at every image.
5. Run `/deck-gate` in a fresh chat before anything leaves the building.

## Prerequisites
- Python 3.11 or later with `pip install python-pptx pillow lxml` (`cairosvg` only for the scripted builder's icons).
- LibreOffice (`soffice` on PATH) for pptx to PDF. Poppler (`pdftoppm` and `pdftotext` on PATH) for PDF to images and text.
- Arial installed (Windows ships it at `C:\Windows\Fonts\arial.ttf`).

## Git note
- The template is 46 MB: under GitHub's 50 MB per-file warning, but every revision adds 46 MB to clone history. Either track it with Git LFS (`git lfs track "templates/*.pptx"` before the first commit) or keep it outside the repo and pass its path with `--template`. Never commit built decks or `qa/` renders; add `decks/` to `.gitignore`.

## Token discipline
- Always-on instructions stay under 60 lines; everything else loads on demand through prompt files or `applyTo` instructions.
- Outline before build: one sentence per slide, approved, before any spec or script is written.
- One deck per chat. Start a new chat for the gate so the reviewer is not anchored on the builder's reasoning.
- Mechanical steps (fill spec, re-render, run checks) go to the cheapest capable model; the outline and copy get the stronger one.

Note: the branding skill's references/ and assets/ folders (colour, typography, logo, hex-loop, copy standards, logo PNG/SVG set) could not be copied because those 23 files carry deny-read permissions for this Windows account in the source. Brand tokens in brand/ cover the same colours and fonts. Lift the permissions in PMK-1 and re-copy if the detailed references are needed.
