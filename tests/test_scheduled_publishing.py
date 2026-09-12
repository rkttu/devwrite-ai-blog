import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("hugo"), "Hugo is required for publication boundary tests")
class ScheduledPublishingTests(unittest.TestCase):
    def test_daily_boundaries_and_links_in_all_languages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config/production").mkdir(parents=True)
            shutil.copyfile(ROOT / "config/production/hugo.toml", root / "config/production/hugo.toml")
            (root / "hugo.toml").write_text('''baseURL = "https://example.org/"
defaultContentLanguage = "ko"
defaultContentLanguageInSubdir = true
[languages.ko]
contentDir = "content/ko"
[languages.en]
contentDir = "content/en"
[languages.ja]
contentDir = "content/ja"
''')
            (root / "layouts/_shortcodes").mkdir(parents=True)
            shutil.copyfile(ROOT / "layouts/_shortcodes/series-link.html", root / "layouts/_shortcodes/series-link.html")
            (root / "layouts/single.html").write_text("<html><body>{{ .Content }}</body></html>")
            (root / "layouts/list.html").write_text('{{ range .Site.RegularPages }}<a href="{{ .RelPermalink }}">{{ .Title }}</a>{{ end }}')
            for lang in ("ko", "en", "ja"):
                for number in range(1, 6):
                    post = root / f"content/{lang}/posts/part-{number}/index.md"
                    post.parent.mkdir(parents=True)
                    links = "\n\n".join('{{< series-link slug="part-%d" text="Part %d" >}}' % (n, n) for n in range(1, 6))
                    post.write_text(f'---\ntitle: "Part {number}"\ndate: "2026-09-{12+number:02}T09:00:00+09:00"\ndraft: false\nslug: "part-{number}"\n---\n\n{links}\n')
                (root / f"content/{lang}/_index.md").write_text('---\ntitle: Home\ndate: "2020-01-01T00:00:00Z"\n---\n')
                (root / f"content/{lang}/posts/baseline.md").write_text('---\ntitle: Baseline\ndate: "2020-01-01T00:00:00Z"\n---\nPublished baseline\n')
                draft = root / f"content/{lang}/posts/unfinished.md"
                draft.write_text('---\ntitle: Unfinished\ndate: "2020-01-01T00:00:00Z"\ndraft: true\n---\nUnfinished draft\n')

            # One second before the first release, then exactly at each daily boundary.
            clocks = ["2026-09-13T08:59:59+09:00"] + [f"2026-09-{day:02}T09:00:00+09:00" for day in range(13, 18)]
            for count, clock in enumerate(clocks):
                with self.subTest(clock=clock):
                    result = subprocess.run(["hugo", "--source", str(root), "--environment", "production", "--enableGitInfo=false", "--clock", clock, "--cleanDestinationDir"], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    for lang in ("ko", "en", "ja"):
                        public = root / "public" / lang
                        self.assertFalse((public / "posts/unfinished/index.html").exists())
                        for number in range(1, 6):
                            post = public / f"posts/part-{number}/index.html"
                            self.assertEqual(post.exists(), number <= count)
                            if post.exists():
                                html = post.read_text()
                                for target in range(1, 6):
                                    self.assertEqual(f'href="/{lang}/posts/part-{target}/"' in html, target <= count)
                                if count < 5:
                                    self.assertIn({"ko": "공개 예정", "en": "Coming soon", "ja": "公開予定"}[lang], html)
                        home = (public / "index.html").read_text()
                        for number in range(1, 6):
                            self.assertEqual(f"/posts/part-{number}/" in home, number <= count)


if __name__ == "__main__":
    unittest.main()
