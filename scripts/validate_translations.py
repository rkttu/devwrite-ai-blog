#!/usr/bin/env python3
"""
번역본 일관성을 검증하는 스크립트

사용법:
    python scripts/validate_translations.py
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_ROOT = PROJECT_ROOT / "content"
ASSETS_ROOT = PROJECT_ROOT / "assets"
STATIC_ROOT = PROJECT_ROOT / "static"
LANGUAGES = ["ko", "en", "ja"]
BASE_LANGUAGE = "ko"


def parse_front_matter(content: str) -> dict:
    """YAML front matter를 간단히 파싱"""
    match = re.match(r"^---\s*\n(.+?)\n---", content, re.DOTALL)
    if not match:
        return {}

    front_matter = {}
    yaml_content = match.group(1)

    # 간단한 YAML 파싱 (단일 값만)
    for line in yaml_content.split("\n"):
        if ":" in line and not line.strip().startswith("-"):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if value:
                front_matter[key] = value

    return front_matter


def get_posts(content_root: Path = CONTENT_ROOT) -> dict:
    """모든 포스트 수집"""
    posts = {}

    for lang in LANGUAGES:
        posts_dir = content_root / lang / "posts"
        if not posts_dir.exists():
            continue

        for post_dir in posts_dir.iterdir():
            if not post_dir.is_dir():
                continue

            index_file = post_dir / "index.md"
            if not index_file.exists():
                continue

            content = index_file.read_text(encoding="utf-8")
            fm = parse_front_matter(content)

            key = post_dir.name
            if key not in posts:
                posts[key] = {}

            posts[key][lang] = {
                "path": index_file,
                "translationKey": fm.get("translationKey"),
                "slug": fm.get("slug"),
                "date": fm.get("date"),
                "cover_image": fm.get("image"),
            }

    return posts


def validate_posts(
    posts: dict,
    *,
    now: datetime | None = None,
    assets_root: Path = ASSETS_ROOT,
    static_root: Path = STATIC_ROOT,
) -> tuple[list[str], list[str]]:
    """수집한 포스트의 오류와 경고를 반환합니다."""
    errors = []
    warnings = []
    validation_time = now or datetime.now(timezone.utc)
    if validation_time.tzinfo is None:
        raise ValueError("now에는 시간대 정보가 필요합니다.")

    for post_name, post in posts.items():
        # 1. 기본 언어에 존재하는지 확인
        if BASE_LANGUAGE not in post:
            errors.append(f"❌ [{post_name}] 기본 언어({BASE_LANGUAGE}) 버전이 없습니다.")
            continue

        base_post = post[BASE_LANGUAGE]

        # 2. translationKey 확인
        if not base_post["translationKey"]:
            errors.append(f"❌ [{post_name}] translationKey가 없습니다. (ko)")

        # 3. slug 확인
        if not base_post["slug"]:
            errors.append(f"❌ [{post_name}] slug가 없습니다. (ko)")

        # 예약 발행을 지원하지 않으므로 미래 날짜를 허용하지 않습니다.
        if not base_post["date"]:
            errors.append(f"❌ [{post_name}] date가 없습니다. (ko)")
        else:
            try:
                published_at = datetime.fromisoformat(base_post["date"].replace("Z", "+00:00"))
                if published_at.tzinfo is None:
                    raise ValueError("timezone required")
                if published_at.astimezone(timezone.utc) > validation_time.astimezone(timezone.utc):
                    errors.append(
                        f"❌ [{post_name}] 미래 날짜는 사용할 수 없습니다: {base_post['date']}"
                    )
            except ValueError:
                errors.append(f"❌ [{post_name}] date 형식이 올바르지 않습니다: {base_post['date']}")

        # 4. 번역본 확인
        for lang in LANGUAGES:
            if lang == BASE_LANGUAGE:
                continue

            if lang not in post:
                warnings.append(f"⚠️  [{post_name}] {lang} 번역본이 없습니다.")
            else:
                lang_post = post[lang]

                # translationKey 일치 확인
                if lang_post["translationKey"] != base_post["translationKey"]:
                    errors.append(
                        f"❌ [{post_name}] translationKey 불일치: "
                        f"ko='{base_post['translationKey']}' vs {lang}='{lang_post['translationKey']}'"
                    )

                # slug 일치 확인
                if lang_post["slug"] != base_post["slug"]:
                    errors.append(
                        f"❌ [{post_name}] slug 불일치: "
                        f"ko='{base_post['slug']}' vs {lang}='{lang_post['slug']}'"
                    )

                if lang_post["date"] != base_post["date"]:
                    errors.append(
                        f"❌ [{post_name}] date 불일치: "
                        f"ko='{base_post['date']}' vs {lang}='{lang_post['date']}'"
                    )

        # 5. Hero 이미지 확인
        if base_post["cover_image"]:
            image_path = Path(base_post["cover_image"])
            candidates = [assets_root / image_path, static_root / image_path]
            if not any(candidate.exists() for candidate in candidates):
                warnings.append(f"⚠️  [{post_name}] Hero 이미지를 찾을 수 없습니다: {base_post['cover_image']}")

    return errors, warnings


def validate():
    """검증 실행"""
    print("🔍 Validating translations...")

    errors, warnings = validate_posts(get_posts())

    # 결과 출력
    print()
    print("=" * 50)

    if not errors and not warnings:
        print("✅ 모든 검증을 통과했습니다!")
    else:
        if errors:
            print(f"\n❌ 오류 ({len(errors)}개):")
            for error in errors:
                print(f"  {error}")

        if warnings:
            print(f"\n⚠️  경고 ({len(warnings)}개):")
            for warning in warnings:
                print(f"  {warning}")

    print()

    # 오류나 경고가 있으면 CI가 실패하도록 exit code 1을 반환합니다.
    if errors or warnings:
        sys.exit(1)


if __name__ == "__main__":
    validate()
