#!/usr/bin/env python3
"""한국어 기본 포스트 번들을 생성합니다."""

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = PROJECT_ROOT / "content" / "ko" / "posts"
KST = timezone(timedelta(hours=9))
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_slug(slug: str) -> str:
    """URL과 파일 경로에 안전한 slug를 반환합니다."""
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError("slug는 영문 소문자, 숫자, 단일 하이픈만 사용할 수 있습니다.")
    return slug


def render_post(slug: str, title: str, now: datetime) -> str:
    """YAML 호환 문자열 이스케이프를 적용한 포스트 초안을 만듭니다."""
    validate_slug(slug)
    title = title.strip()
    if not title:
        raise ValueError("제목을 입력해 주세요.")

    timestamp = now.astimezone(KST).isoformat(timespec="seconds")
    quoted_title = json.dumps(title, ensure_ascii=False)
    quoted_slug = json.dumps(slug)
    return f'''---
title: {quoted_title}
date: {timestamp}
draft: true
slug: {quoted_slug}
description: ""
tags: []
categories: []
translationKey: {quoted_slug}
cover:
  image: ""
  alt: ""
tldr: ""
---

여기에 내용을 작성하세요.
'''


def create_post(
    slug: str,
    title: str,
    content_root: Path = CONTENT_ROOT,
    now: datetime | None = None,
) -> Path:
    """현재 날짜를 포함한 페이지 번들을 생성하고 경로를 반환합니다."""
    now = now or datetime.now(KST)
    content = render_post(slug, title, now)
    post_dir = content_root / f"{now.astimezone(KST):%Y-%m-%d}-{slug}"
    post_path = post_dir / "index.md"

    if post_dir.exists():
        raise FileExistsError(f"이미 존재하는 포스트입니다: {post_dir}")

    post_dir.mkdir(parents=True)
    post_path.write_text(content, encoding="utf-8")
    return post_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True, help="영문 소문자와 하이픈으로 구성한 URL 식별자")
    parser.add_argument("--title", required=True, help="한국어 포스트 제목")
    args = parser.parse_args()

    try:
        post_path = create_post(args.slug, args.title)
    except (ValueError, FileExistsError) as error:
        parser.exit(1, f"오류: {error}\n")

    print(f"새 포스트를 생성했습니다: {post_path}")
    print("내용, description, tags, tldr, Hero 이미지를 작성한 뒤 draft를 false로 바꾸면 됩니다.")


if __name__ == "__main__":
    main()
