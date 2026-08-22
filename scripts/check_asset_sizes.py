#!/usr/bin/env python3
"""저장소에 포함된 이미지 원본의 최대 크기를 검사합니다."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_ROOTS = [PROJECT_ROOT / "assets" / "images", PROJECT_ROOT / "static" / "images"]
IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
MAX_IMAGE_BYTES = 1_000_000


def find_oversized_images(
    image_roots: list[Path] = IMAGE_ROOTS,
    *,
    project_root: Path = PROJECT_ROOT,
    max_image_bytes: int = MAX_IMAGE_BYTES,
) -> list[tuple[Path, int]]:
    """제한을 초과한 이미지 경로와 크기를 반환합니다."""
    oversized = []
    for root in image_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                size = path.stat().st_size
                if size > max_image_bytes:
                    oversized.append((path.relative_to(project_root), size))
    return sorted(oversized)


def main() -> None:
    oversized = find_oversized_images()

    if oversized:
        print("1MB를 초과한 이미지가 있습니다.")
        for path, size in oversized:
            print(f"- {path}: {size:,}바이트")
        raise SystemExit(1)
    print("이미지 원본 크기 검사를 통과했습니다.")


if __name__ == "__main__":
    main()
