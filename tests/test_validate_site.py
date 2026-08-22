import tempfile
import unittest
from pathlib import Path

from scripts.validate_site import REQUIRED_FILES, validate


def create_valid_site(root: Path) -> None:
    for filename in REQUIRED_FILES:
        (root / filename).write_text("placeholder", encoding="utf-8")

    (root / "index.html").write_text(
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"WebSite"}'
        "</script>",
        encoding="utf-8",
    )
    (root / "404.html").write_text(
        '<meta name="robots" content="noindex, nofollow">'
        '<section data-lang="ko"></section>'
        '<section data-lang="en"></section>'
        '<section data-lang="ja"></section>',
        encoding="utf-8",
    )
    for language in ("ko", "en", "ja"):
        language_root = root / language
        language_root.mkdir()
        (language_root / "llms.txt").write_text(
            f"https://devwrite.ai/{language}/posts/sample/",
            encoding="utf-8",
        )


class SiteValidationTests(unittest.TestCase):
    def test_accepts_required_outputs_and_json_ld(self):
        with tempfile.TemporaryDirectory() as directory:
            public_dir = Path(directory)
            create_valid_site(public_dir)

            self.assertEqual(validate(public_dir), [])

    def test_reports_missing_internal_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            public_dir = Path(directory)
            create_valid_site(public_dir)
            (public_dir / "index.html").write_text(
                '<a href="/missing/">missing</a>'
                '<script type="application/ld+json">'
                '{"@context":"https://schema.org","@type":"WebSite"}'
                "</script>",
                encoding="utf-8",
            )

            errors = validate(public_dir)

            self.assertTrue(any("존재하지 않는 내부 참조: /missing/" in error for error in errors))

    def test_reports_invalid_json_ld(self):
        with tempfile.TemporaryDirectory() as directory:
            public_dir = Path(directory)
            create_valid_site(public_dir)
            (public_dir / "index.html").write_text(
                '<script type="application/ld+json">{invalid}</script>',
                encoding="utf-8",
            )

            errors = validate(public_dir)

            self.assertTrue(any("JSON-LD 파싱 실패" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
