"""Tests for generic shape detection by computed style."""

import tempfile
from pathlib import Path

from apograph.extract import extract_from_html


RULE_HTML = """<!DOCTYPE html><html><body>
<div class="slide" style="width:800px;height:400px;background:#fff;position:relative">
  <div style="background:#cccccc;height:2px;width:100%"></div>
  <p style="color:#333;font-size:14px">Some text</p>
</div>
</body></html>"""

CIRCLE_HTML = """<!DOCTYPE html><html><body>
<div class="slide" style="width:800px;height:400px;background:#fff;position:relative">
  <div style="width:40px;height:40px;border-radius:50%;background:#eeeeee"></div>
  <p style="color:#333;font-size:14px">Some text</p>
</div>
</body></html>"""


def test_horizontal_rule_detected_by_style():
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as tmp:
        tmp.write(RULE_HTML)
        tmp_path = Path(tmp.name)
    try:
        data = extract_from_html(tmp_path)
        rules = [e for e in data.elements if e.get("isHorizontalRule")]
        assert len(rules) >= 1, f"Expected horizontal rule, got {rules}"
        assert rules[0]["ruleBgColor"] is not None
    finally:
        tmp_path.unlink(missing_ok=True)


def test_circle_detected_by_style():
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as tmp:
        tmp.write(CIRCLE_HTML)
        tmp_path = Path(tmp.name)
    try:
        data = extract_from_html(tmp_path)
        circles = [e for e in data.elements if e.get("isCirclePlaceholder")]
        assert len(circles) >= 1, f"Expected circle placeholder, got {circles}"
        assert circles[0]["circleBgColor"] is not None
    finally:
        tmp_path.unlink(missing_ok=True)
