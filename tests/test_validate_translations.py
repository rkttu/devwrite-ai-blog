import unittest

from scripts.validate_translations import validate_posts



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
        errors, warnings = validate_posts(translated_post())

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_accepts_future_publication_date(self):
        posts = translated_post("2099-08-23T10:00:00+09:00")

        errors, _ = validate_posts(posts)

        self.assertEqual(errors, [])

    def test_rejects_invalid_or_naive_dates(self):
        for date in ("not-a-date", "2026-09-13", "2026-09-13T09:00:00"):
            with self.subTest(date=date):
                errors, _ = validate_posts(translated_post(date))
                self.assertTrue(any("date 형식" in error for error in errors))

    def test_rejects_inconsistent_publication_state(self):
        posts = translated_post()
        posts["2026-08-22-sample-post"]["ko"]["draft"] = "false"
        posts["2026-08-22-sample-post"]["en"]["publishDate"] = "2099-09-13T09:00:00+09:00"
        errors, _ = validate_posts(posts)
        self.assertTrue(any("draft 불일치" in error for error in errors))
        self.assertTrue(any("publishDate 불일치" in error for error in errors))

    def test_rejects_invalid_publish_date(self):
        posts = translated_post()
        for post in posts["2026-08-22-sample-post"].values():
            post["publishDate"] = "2026-09-13T09:00:00"
        errors, _ = validate_posts(posts)
        self.assertTrue(any("publishDate 형식" in error for error in errors))

    def test_missing_translations_still_warn(self):
        posts = translated_post()
        del posts["2026-08-22-sample-post"]["ja"]
        _, warnings = validate_posts(posts)
        self.assertTrue(any("ja 번역본" in warning for warning in warnings))

    def test_rejects_translation_metadata_mismatch(self):
        posts = translated_post()
        posts["2026-08-22-sample-post"]["en"]["slug"] = "different-slug"
        posts["2026-08-22-sample-post"]["ja"]["date"] = "2026-08-21T10:00:00+09:00"

        errors, _ = validate_posts(posts)

        self.assertTrue(any("slug 불일치" in error for error in errors))
        self.assertTrue(any("date 불일치" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
