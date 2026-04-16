"""CLI entry point for apograph."""

from __future__ import annotations

import json
from pathlib import Path

import cyclopts

from apograph import __version__
from apograph.convert import convert
from apograph.extract import extract_from_html

app = cyclopts.App(
    name="apograph",
    help="Convert HTML slides to PPTX with layout fidelity.",
    version=__version__,
)


@app.default
def run(
    html: Path,
    *,
    output: Path | None = None,
    images: Path | None = None,
    slide_width: float = 13.333,
    slide_height: float = 7.5,
    accent_color: str | None = None,
    font: str | None = None,
    hybrid: bool = False,
    as_json: bool = False,
    extract_only: bool = False,
) -> None:
    """Convert an HTML slide to PPTX.

    Args:
        html: Path to HTML slide file.
        output: Output PPTX path (default: same name with .pptx extension).
        images: Directory containing images referenced in the HTML.
        slide_width: PPTX slide width in inches (default: 13.333 for 16:9).
        slide_height: PPTX slide height in inches (default: 7.5 for 16:9).
        accent_color: CSS color for top accent bar (e.g. 'rgb(219,0,17)').
        font: Override all text with this font family.
        hybrid: Pixel-perfect background image + editable text overlays.
        as_json: Output extracted layout as JSON (for debugging).
        extract_only: Only extract layout, don't generate PPTX.
    """
    html = html.expanduser().resolve()
    if not html.exists():
        raise SystemExit(f"File not found: {html}")

    # Extract layout from HTML
    data = extract_from_html(html, hybrid=hybrid)

    if extract_only or as_json:
        payload = {
            "slide_width_px": data.width_px,
            "slide_height_px": data.height_px,
            "element_count": len(data.elements),
            "elements": data.elements,
        }
        print(json.dumps(payload, indent=2))
        return

    # Resolve output path
    if output is None:
        output = html.with_suffix(".pptx")
    output = output.expanduser().resolve()

    # Resolve image directory
    image_dir = None
    if images:
        image_dir = images.expanduser().resolve()
    else:
        # Try to find images relative to HTML file
        image_dir = html.parent

    result = convert(
        data,
        output,
        slide_width_in=slide_width,
        slide_height_in=slide_height,
        image_base_dir=image_dir,
        accent_color=accent_color,
        font_override=font,
        hybrid=hybrid,
    )
    print(f"Saved: {result}")


def main() -> None:
    """Entry point."""
    app()
