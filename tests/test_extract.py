import unittest

from qzone_text_exporter import extract


class TestExtract(unittest.TestCase):
    def test_extract_nested_div_not_truncated(self) -> None:
        html = (
            "<html><body>"
            "<div id=\"blogDetailDiv\">"
            "<div class=\"blog_details_20120222\">"
            "<div><div><span>Hello</span><br/>"
            "<div><span>Nested</span> <span>Text</span></div>"
            "<img src=\"x.jpg\"/>"
            "</div></div>"
            "</div>"
            "<div class=\"blog_footer\">FOOTER</div>"
            "</body></html>"
        ).encode("gb18030", errors="ignore")

        text = extract.html_to_text(html)
        self.assertIn("Hello", text)
        self.assertIn("Nested Text", text)
        self.assertNotIn("FOOTER", text)

    def test_extract_skips_scripts(self) -> None:
        html = (
            "<html><body>"
            "<div id=\"blogDetailDiv\">"
            "Hi<script>var x=1;</script>There"
            "</div><div class=\"blog_footer\">FOOTER</div>"
            "</body></html>"
        ).encode("gb18030", errors="ignore")
        text = extract.html_to_text(html)
        self.assertIn("Hi", text)
        self.assertIn("There", text)
        self.assertNotIn("var x", text)


if __name__ == "__main__":
    unittest.main()

