import tempfile
import unittest
from pathlib import Path

from scripts.check_asset_sizes import find_oversized_images


class AssetSizeValidationTests(unittest.TestCase):
    def test_reports_only_images_over_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            image_root = project_root / "images"
            image_root.mkdir()
            (image_root / "small.jpg").write_bytes(b"x" * 10)
            (image_root / "large.png").write_bytes(b"x" * 11)
            (image_root / "large.txt").write_bytes(b"x" * 20)

            oversized = find_oversized_images(
                [image_root],
                project_root=project_root,
                max_image_bytes=10,
            )

            self.assertEqual(oversized, [(Path("images/large.png"), 11)])


if __name__ == "__main__":
    unittest.main()
