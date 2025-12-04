#!/usr/bin/env python3
"""
새 블로그 포스트를 생성하는 스크립트

사용법:
    python scripts/new_post.py --slug "my-first-post" --title "나의 첫 번째 포스트"
"""

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONTENT_ROOT = PROJECT_ROOT / "content" / "ko" / "posts"


def create_post(slug: str, title: str):
    """새 포스트 생성"""
    post_path = CONTENT_ROOT / f"{slug}.md"
    
    # 이미 존재하는지 확인
    if post_path.exists():
        print(f"❌ 이미 존재하는 포스트입니다: {post_path}")
        sys.exit(1)
    
    # 날짜 생성 (KST)
    kst = timezone(timedelta(hours=9))
    date = datetime.now(kst).strftime("%Y-%m-%dT%H:%M:%S%z")
    # +0900 형식을 +09:00 형식으로 변환
    date = date[:-2] + ":" + date[-2:]
    
    # Front matter 템플릿
    content = f'''---
title: "{title}"
date: {date}
draft: true
slug: "{slug}"
tags: []
categories: []
translationKey: "{slug}"
cover:
  image: ""
  alt: ""
tldr: ""
---

여기에 내용을 작성하세요.
'''
    
    # 디렉터리 생성
    post_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 파일 생성
    post_path.write_text(content, encoding="utf-8")
    
    print(f"✅ 새 포스트가 생성되었습니다:")
    print(f"   {post_path}")
    print()
    print("다음 단계:")
    print("  1. 포스트 내용 작성")
    print("  2. tags, categories 추가")
    print("  3. tldr 작성")
    print("  4. Hero 이미지 추가 (선택)")
    print("  5. draft: false로 변경")
    print("  6. 번역본 생성 (en, ja)")


def main():
    parser = argparse.ArgumentParser(description="새 블로그 포스트 생성")
    parser.add_argument("--slug", required=True, help="URL에 사용될 슬러그 (영문, 하이픈 사용)")
    parser.add_argument("--title", required=True, help="포스트 제목 (한국어)")
    
    args = parser.parse_args()
    create_post(args.slug, args.title)


if __name__ == "__main__":
    main()
