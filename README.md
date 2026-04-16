# apograph

Convert HTML slides to PPTX with layout fidelity.

Playwright renders the HTML, extracts every element's computed position and styles, then python-pptx places shapes at proportional positions. The HTML is the single source of truth.

## Install

```bash
pip install apograph
playwright install chromium
```

## Usage

```bash
apograph slide.html                          # → slide.pptx
apograph slide.html --output deck.pptx       # custom output path
apograph slide.html --images ./headshots     # image directory
apograph slide.html --accent-color "rgb(219,0,17)"  # top accent bar
apograph slide.html --font "Century Gothic"  # override font
apograph slide.html --extract-only           # dump layout as JSON
```
