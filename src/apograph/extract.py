"""Extract element layout and styles from rendered HTML via Playwright."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import sync_playwright

JS_EXTRACT = """() => {
    const slide = document.querySelector('.slide') || document.body;
    const slideRect = slide.getBoundingClientRect();
    const results = [];

    function extract(el, depth) {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        const x = rect.left - slideRect.left;
        const y = rect.top - slideRect.top;
        const w = rect.width;
        const h = rect.height;
        if (w < 1 || h < 1) return;

        const tag = el.tagName.toLowerCase();
        const cls = el.className || '';
        // Text extraction: leaf nodes OR elements with only <br>/inline children
        const innerHTML = el.innerHTML || '';
        const hasLineBreak = innerHTML.includes('<br');
        const isLeafText = el.childNodes.length === 1 && el.childNodes[0].nodeType === 3;
        // Element with <br> but no block children = text element with line breaks
        const blockTags = new Set(['div','ul','ol','li','p','section','article','header','footer','nav','main']);
        const hasBlockChild = Array.from(el.children).some(c => blockTags.has(c.tagName.toLowerCase()));
        const isBrText = hasLineBreak && !hasBlockChild && el.children.length <= 2;
        const text = (isLeafText || isBrText) && el.textContent.trim().length > 0
            ? null : null;  // computed below
        // Use innerText for <br> elements (preserves newlines), textContent for leaf
        const capturedText = isBrText ? el.innerText.trim()
            : isLeafText ? el.textContent.trim()
            : null;

        const info = {
            tag, cls, text: capturedText, x, y, w, h,
            fontSize: parseFloat(style.fontSize),
            fontWeight: style.fontWeight,
            fontStyle: style.fontStyle,
            color: style.color,
            backgroundColor: style.backgroundColor,
            textTransform: style.textTransform,
            letterSpacing: style.letterSpacing,
            lineHeight: style.lineHeight,
            depth
        };

        if (tag === 'img') {
            info.src = el.getAttribute('src');
            info.alt = el.getAttribute('alt');
            info.isImage = true;
        }
        if (cls.includes && cls.includes('person-placeholder')) {
            info.isPlaceholder = true;
        }

        results.push(info);
        // Skip recursing into <br>-text elements to avoid duplicate child text
        if (isBrText) return;
        for (const child of el.children) {
            extract(child, depth + 1);
        }
    }

    extract(slide, 0);

    return {
        slideWidth: slideRect.width,
        slideHeight: slideRect.height,
        elements: results
    };
}"""


@dataclass
class SlideData:
    """Extracted layout data from an HTML slide."""

    width_px: float
    height_px: float
    elements: list[dict]
    background_image: bytes | None = None


def extract_from_html(
    html_path: Path,
    viewport_width: int = 1200,
    viewport_height: int = 750,
    *,
    hybrid: bool = False,
) -> SlideData:
    """Render HTML in headless Chromium and extract all element positions + styles.

    If hybrid=True, also captures a screenshot with text hidden (for background image).
    """
    html_path = html_path.resolve()
    if not html_path.exists():
        msg = f"HTML file not found: {html_path}"
        raise FileNotFoundError(msg)

    bg_image: bytes | None = None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        device_scale = 2 if hybrid else 1
        page = browser.new_page(
            viewport={"width": viewport_width, "height": viewport_height},
            device_scale_factor=device_scale,
        )
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(1000)

        result = page.evaluate(JS_EXTRACT)

        if hybrid:
            # Hide all text elements, screenshot the visual layer only
            page.evaluate("""() => {
                const slide = document.querySelector('.slide') || document.body;
                const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
                const textNodes = [];
                while (walker.nextNode()) textNodes.push(walker.currentNode);
                // Make all text transparent (keeps layout, hides text)
                const style = document.createElement('style');
                style.textContent = `
                    .slide, .slide * {
                        color: transparent !important;
                        -webkit-text-fill-color: transparent !important;
                    }
                `;
                document.head.appendChild(style);
            }""")
            page.wait_for_timeout(200)
            slide_el = page.query_selector(".slide") or page.query_selector("body")
            if slide_el:
                bg_image = slide_el.screenshot(type="png")

        browser.close()

    return SlideData(
        width_px=result["slideWidth"],
        height_px=result["slideHeight"],
        elements=result["elements"],
        background_image=bg_image,
    )
