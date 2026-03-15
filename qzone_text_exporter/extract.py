from __future__ import annotations

import html
import re
from html.parser import HTMLParser


class QzoneHTMLToText(HTMLParser):
    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "div",
        "dl",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tr",
        "ul",
    }

    SKIP_TAGS = {"img", "script", "style", "svg", "noscript", "iframe", "object"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self.skip_stack.append(tag)
            return
        if self.skip_stack:
            return
        if tag == "br":
            self.parts.append("\n")
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_stack and tag == self.skip_stack[-1]:
            self.skip_stack.pop()
            return
        if self.skip_stack:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_stack:
            return
        self.parts.append(data)

    def get_text(self) -> str:
        text = html.unescape("".join(self.parts)).replace("\xa0", " ")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        compact: list[str] = []
        blank = False
        for line in lines:
            if not line:
                if compact and not blank:
                    compact.append("")
                blank = True
                continue
            compact.append(line)
            blank = False
        return "\n".join(compact).strip()


def select_main_html(html_text: str) -> str:
    markers = [
        ('id="blogDetailDiv"', ['<div id="attachList"', '<div class="blog_footer"', "</body>"]),
        ("id='blogDetailDiv'", ['<div id="attachList"', '<div class="blog_footer"', "</body>"]),
        ('class="blog_detail"', ['<div id="attachList"', '<div class="blog_footer"', "</body>"]),
    ]
    for start_marker, end_markers in markers:
        start = html_text.find(start_marker)
        if start == -1:
            continue
        start = html_text.rfind("<div", 0, start)
        if start == -1:
            continue
        end_positions = [html_text.find(marker, start) for marker in end_markers]
        end_positions = [pos for pos in end_positions if pos != -1]
        if end_positions:
            return html_text[start : min(end_positions)]
    body = re.search(r"<body[^>]*>(.*)</body>", html_text, flags=re.I | re.S)
    return body.group(1) if body else html_text


def html_to_text(raw_html: bytes, *, encoding: str = "gb18030") -> str:
    html_text = raw_html.decode(encoding, errors="ignore")
    main_html = select_main_html(html_text)
    parser = QzoneHTMLToText()
    parser.feed(main_html)
    return parser.get_text()

