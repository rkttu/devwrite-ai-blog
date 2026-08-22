import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.new_post import create_post, render_post, validate_slug


KST = timezone(timedelta(hours=9))
FIXED_TIME = datetime(2026, 8, 22, 10, 30, 0, tzinfo=KST)


class SlugValidationTests(unittest.TestCase):
    def test_accepts_lowercase_kebab_case(self):
        self.assertEqual(validate_slug("hugo-165"), "hugo-165")

    def test_rejects_path_and_uppercase_characters(self):
        for slug in ("../outside", "Hugo-post", "hugo--post", "hugo_post"):
            with self.subTest(slug=slug):
                with self.assertRaises(ValueError):
                    validate_slug(slug)


class PostRenderingTests(unittest.TestCase):
    def test_escapes_title_as_yaml_compatible_json_string(self):
        content = render_post("quoted-title", 'C#: "인용"과 역슬래시 \\', FIXED_TIME)
        self.assertIn('title: "C#: \\"인용\\"과 역슬래시 \\\\"', content)
        self.assertIn('description: ""', content)
        self.assertIn("date: 2026-08-22T10:30:00+09:00", content)

    def test_creates_a_dated_page_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            path = create_post(
                "new-post",
                "새 글",
                content_root=Path(directory),
                now=FIXED_TIME,
            )
            self.assertEqual(path.relative_to(directory), Path("2026-08-22-new-post/index.md"))
            self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
