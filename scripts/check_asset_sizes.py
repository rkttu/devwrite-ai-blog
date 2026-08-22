#!/usr/bin/env python3
"""저장소에 포함된 이미지 원본의 최대 크기를 검사합니다."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_ROOTS = [PROJECT_ROOT / "assets" / "images", PROJECT_ROOT / "static" / "images"]
IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
MAX_IMAGE_BYTES = 1_000_000


def main() -> None:
    oversized = []
    for root in IMAGE_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                size = path.stat().st_size
                if size > MAX_IMAGE_BYTES:
                    oversized.append((path.relative_to(PROJECT_ROOT), size))

    if oversized:
        print("1MB를 초과한 이미지가 있습니다.")
        for path, size in oversized:
            print(f"- {path}: {size:,}바이트")
        raise SystemExit(1)
    print("이미지 원본 크기 검사를 통과했습니다.")


if __name__ == "__main__":
    main()
