import unittest
from datetime import datetime, timezone

from scripts.validate_translations import validate_posts


NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


def translated_post(date: str = "2026-08-22T10:00:00+09:00") -> dict:
    post = {}
    for language in ("ko", "en", "ja"):
        post[language] = {
            "path": None,
            "translationKey": "sample-post",
            "slug": "sample-post",
            "date": date,
            "cover_image": None,
        }
    return {"2026-08-22-sample-post": post}


class TranslationValidationTests(unittest.TestCase):
    def test_accepts_consistent_translations(self):
        errors, warnings = validate_posts(translated_post(), now=NOW)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_rejects_future_publication_date(self):
        posts = translated_post("2026-08-23T10:00:00+09:00")

        errors, _ = validate_posts(posts, now=NOW)

        self.assertTrue(any("미래 날짜" in error for error in errors))

    def test_rejects_translation_metadata_mismatch(self):
        posts = translated_post()
        posts["2026-08-22-sample-post"]["en"]["slug"] = "different-slug"
        posts["2026-08-22-sample-post"]["ja"]["date"] = "2026-08-21T10:00:00+09:00"

        errors, _ = validate_posts(posts, now=NOW)

        self.assertTrue(any("slug 불일치" in error for error in errors))
        self.assertTrue(any("date 불일치" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
