#!/usr/bin/env python3
"""
Unsplash에서 Hero 이미지를 다운로드하는 스크립트

사용법:
    python scripts/fetch_hero_image.py --slug "my-post" --keywords "coding,programming"
"""

import argparse
import sys
import urllib.request
import urllib.error
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
IMAGES_DIR = PROJECT_ROOT / "assets" / "images" / "posts"


def fetch_image(slug: str, keywords: str, width: int = 1200, height: int = 630):
    """Unsplash에서 이미지 다운로드"""
    output_path = IMAGES_DIR / f"{slug}.jpg"
    
    # 디렉터리 생성
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 이미 존재하는지 확인
    if output_path.exists():
        response = input("이미지가 이미 존재합니다. 덮어쓰시겠습니까? (y/N): ")
        if response.lower() != "y":
            print("취소되었습니다.")
            return
    
    # Unsplash Source URL
    url = f"https://source.unsplash.com/{width}x{height}/?{keywords}"
    
    print(f"🖼️  Unsplash에서 이미지를 다운로드합니다...")
    print(f"   URL: {url}")
    
    try:
        # 이미지 다운로드
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(request) as response:
            image_data = response.read()
        
        # 파일 저장
        output_path.write_bytes(image_data)
        
        print(f"✅ 이미지가 저장되었습니다:")
        print(f"   {output_path}")
        print()
        print("Front matter에 추가:")
        print(f'''cover:
  image: "images/posts/{slug}.jpg"
  alt: "이미지 설명을 입력하세요"''')
    
    except urllib.error.URLError as e:
        print(f"❌ 이미지 다운로드 실패: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Unsplash에서 Hero 이미지 다운로드")
    parser.add_argument("--slug", required=True, help="포스트 슬러그 (파일명으로 사용)")
    parser.add_argument("--keywords", required=True, help="Unsplash 검색 키워드 (쉼표로 구분)")
    parser.add_argument("--width", type=int, default=1200, help="이미지 너비 (기본값: 1200)")
    parser.add_argument("--height", type=int, default=630, help="이미지 높이 (기본값: 630)")
    
    args = parser.parse_args()
    fetch_image(args.slug, args.keywords, args.width, args.height)


if __name__ == "__main__":
    main()
