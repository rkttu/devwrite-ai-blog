#!/usr/bin/env python3
"""
번역본 일관성을 검증하는 스크립트

사용법:
    python scripts/validate_translations.py
"""

import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_ROOT = PROJECT_ROOT / "content"
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


def get_posts() -> dict:
    """모든 포스트 수집"""
    posts = {}
    
    for lang in LANGUAGES:
        posts_dir = CONTENT_ROOT / lang / "posts"
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
                "cover_image": fm.get("image"),
            }
    
    return posts


def validate():
    """검증 실행"""
    errors = []
    warnings = []
    
    print("🔍 Validating translations...")
    
    posts = get_posts()
    
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
        
        # 5. Hero 이미지 확인
        if base_post["cover_image"]:
            image_path = STATIC_ROOT / base_post["cover_image"]
            if not image_path.exists():
                warnings.append(f"⚠️  [{post_name}] Hero 이미지를 찾을 수 없습니다: {base_post['cover_image']}")
    
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
    
    # 오류가 있으면 exit code 1
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    validate()
