import unittest

from scripts.detect_published_posts import is_published
from scripts.kit_broadcast import build_broadcast_html, parse_front_matter_text


class FrontMatterTests(unittest.TestCase):
    def test_detects_draft_and_published_posts(self):
        self.assertFalse(is_published("---\ndraft: true\n---\n"))
        self.assertTrue(is_published("---\ndraft: false\n---\n"))

    def test_parses_title_with_colon(self):
        metadata = parse_front_matter_text(
            '---\ntitle: "C#: 새 글"\ndraft: false\n---\n'
        )
        self.assertEqual(metadata["title"], "C#: 새 글")


class BroadcastHtmlTests(unittest.TestCase):
    def test_escapes_content_and_url(self):
        content = build_broadcast_html(
            {"title": "<script>", "tldr": "A & B"},
            "https://example.com/?a=1&b=2",
            "ko",
        )
        self.assertIn("&lt;script&gt;", content)
        self.assertIn("A &amp; B", content)
        self.assertIn("a=1&amp;b=2", content)


if __name__ == "__main__":
    unittest.main()
