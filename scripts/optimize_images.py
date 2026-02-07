#!/usr/bin/env python3
"""
Hero 이미지를 WebP 형식으로 변환하고 리사이즈하는 스크립트

static/images/posts/ 디렉터리의 JPG/PNG Hero 이미지를 WebP로 변환합니다.
변환 후 front matter의 cover.image 경로를 .webp로 업데이트할 수 있습니다.

의존성:
    pip install Pillow

사용법:
    # 모든 Hero 이미지를 WebP로 변환
    python scripts/optimize_images.py

    # 특정 슬러그의 이미지만 변환
    python scripts/optimize_images.py --slug "my-post"

    # 최대 너비 지정 (기본값: 1200px)
    python scripts/optimize_images.py --max-width 1600

    # WebP 품질 지정 (기본값: 85)
    python scripts/optimize_images.py --quality 80

    # 변환 후 원본 JPG/PNG 삭제
    python scripts/optimize_images.py --delete-originals

    # front matter의 cover.image 경로도 .webp로 업데이트
    python scripts/optimize_images.py --update-frontmatter
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("❌ Pillow 패키지가 필요합니다. 다음 명령으로 설치하세요:")
    print("   pip install Pillow")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "posts"
CONTENT_DIR = PROJECT_ROOT / "content"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
LANGUAGES = ["ko", "en", "ja"]


def get_image_files(slug: str | None = None) -> list[Path]:
    """변환 대상 이미지 파일 목록을 반환합니다."""
    if not IMAGES_DIR.exists():
        print(f"❌ 이미지 디렉터리가 없습니다: {IMAGES_DIR}")
        sys.exit(1)

    if slug:
        # 특정 슬러그만 검색
        candidates = []
        for ext in SUPPORTED_EXTENSIONS:
            path = IMAGES_DIR / f"{slug}{ext}"
            if path.exists():
                candidates.append(path)
        return candidates
    else:
        # 모든 이미지 검색
        return [
            f for f in IMAGES_DIR.iterdir()
            if f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]


def convert_to_webp(
    image_path: Path,
    max_width: int = 1200,
    quality: int = 85,
) -> Path | None:
    """이미지를 WebP로 변환하고 리사이즈합니다."""
    output_path = image_path.with_suffix(".webp")

    try:
        with Image.open(image_path) as img:
            original_size = image_path.stat().st_size
            original_dimensions = img.size

            # EXIF 회전 정보 적용
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)

            # 리사이즈 (최대 너비 초과 시에만)
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            # RGBA인 경우 RGB로 변환 (WebP는 알파 채널 지원하지만, 불필요한 경우 제거)
            if img.mode == "RGBA":
                # 알파 채널이 실제로 사용되는지 확인
                alpha = img.split()[-1]
                if alpha.getextrema() == (255, 255):
                    img = img.convert("RGB")

            # WebP로 저장
            img.save(output_path, "WebP", quality=quality, method=4)

            new_size = output_path.stat().st_size
            reduction = (1 - new_size / original_size) * 100

            print(f"  ✅ {image_path.name}")
            print(f"     {original_dimensions[0]}x{original_dimensions[1]} → {img.width}x{img.height}")
            print(f"     {original_size / 1024:.1f}KB → {new_size / 1024:.1f}KB ({reduction:.1f}% 절감)")

            return output_path

    except Exception as e:
        print(f"  ❌ {image_path.name}: 변환 실패 - {e}")
        return None


def update_frontmatter(slug: str, old_ext: str):
    """모든 언어의 front matter에서 cover.image 경로를 .webp로 업데이트합니다."""
    old_image = f"images/posts/{slug}{old_ext}"
    new_image = f"images/posts/{slug}.webp"
    updated_files = []

    for lang in LANGUAGES:
        # Page Bundle 구조: content/{lang}/posts/*/index.md
        posts_dir = CONTENT_DIR / lang / "posts"
        if not posts_dir.exists():
            continue

        for post_dir in posts_dir.iterdir():
            if not post_dir.is_dir():
                continue

            index_md = post_dir / "index.md"
            if not index_md.exists():
                continue

            content = index_md.read_text(encoding="utf-8")

            # cover.image 패턴 검색 (slug와 매칭)
            if old_image in content:
                new_content = content.replace(old_image, new_image)
                index_md.write_text(new_content, encoding="utf-8")
                updated_files.append(str(index_md.relative_to(PROJECT_ROOT)))

    if updated_files:
        print(f"     📝 front matter 업데이트:")
        for f in updated_files:
            print(f"        {f}")


def main():
    parser = argparse.ArgumentParser(
        description="Hero 이미지를 WebP로 변환하고 리사이즈합니다."
    )
    parser.add_argument(
        "--slug",
        help="특정 포스트 슬러그의 이미지만 변환",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=1200,
        help="최대 이미지 너비 (기본값: 1200)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="WebP 품질 (1-100, 기본값: 85)",
    )
    parser.add_argument(
        "--delete-originals",
        action="store_true",
        help="변환 후 원본 JPG/PNG 파일 삭제",
    )
    parser.add_argument(
        "--update-frontmatter",
        action="store_true",
        help="front matter의 cover.image 경로를 .webp로 업데이트",
    )

    args = parser.parse_args()

    # 대상 이미지 검색
    image_files = get_image_files(args.slug)

    if not image_files:
        if args.slug:
            print(f"⚠️  '{args.slug}'에 해당하는 이미지를 찾을 수 없습니다.")
        else:
            print("⚠️  변환할 이미지가 없습니다.")
        return

    # 이미 WebP가 존재하는 이미지 필터링
    to_convert = []
    for img in image_files:
        webp_path = img.with_suffix(".webp")
        if webp_path.exists():
            print(f"  ⏭️  {img.name}: 이미 WebP가 존재합니다 ({webp_path.name})")
        else:
            to_convert.append(img)

    if not to_convert:
        print("✅ 모든 이미지가 이미 WebP로 변환되어 있습니다.")
        return

    print(f"🖼️  {len(to_convert)}개 이미지를 WebP로 변환합니다...")
    print(f"   설정: 최대 너비={args.max_width}px, 품질={args.quality}")
    print()

    converted = []
    for image_path in sorted(to_convert):
        result = convert_to_webp(image_path, args.max_width, args.quality)
        if result:
            converted.append((image_path, result))

    print()

    # front matter 업데이트
    if args.update_frontmatter and converted:
        print("📝 front matter 경로를 업데이트합니다...")
        for original, webp in converted:
            slug = original.stem
            update_frontmatter(slug, original.suffix)
        print()

    # 원본 삭제
    if args.delete_originals and converted:
        print("🗑️  원본 파일을 삭제합니다...")
        for original, _ in converted:
            original.unlink()
            print(f"  🗑️  {original.name} 삭제됨")
        print()

    # 요약
    total_original = sum(orig.stat().st_size for orig, _ in converted if orig.exists())
    total_webp = sum(webp.stat().st_size for _, webp in converted)

    if not args.delete_originals and converted:
        total_original = sum(
            orig.stat().st_size for orig, _ in converted
        )

    print(f"✅ 변환 완료: {len(converted)}/{len(to_convert)}개 성공")

    if not args.delete_originals:
        print()
        print("💡 원본 파일을 삭제하려면 --delete-originals 옵션을 사용하세요.")
        print("💡 front matter를 업데이트하려면 --update-frontmatter 옵션을 사용하세요.")


if __name__ == "__main__":
    main()
