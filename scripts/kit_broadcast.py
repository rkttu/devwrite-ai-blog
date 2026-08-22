#!/usr/bin/env python3
"""
Kit Newsletter Broadcast Script

Hugo 블로그에 새 포스트가 추가되면 Kit API를 통해
뉴스레터 브로드캐스트를 생성합니다.

환경변수:
  KIT_API_KEY       - Kit API v4 키 (필수)
  KIT_SEND_AT       - 예약 발송 시각 ISO8601 (선택, 없으면 드래프트 저장)
  BASE_URL          - 블로그 기본 URL (기본값: https://devwrite.ai)
  DEFAULT_LANG      - 기본 언어 (기본값: ko)
"""

import html as html_lib
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


API_URL = "https://api.kit.com/v4/broadcasts"
REQUEST_TIMEOUT_SECONDS = 30


def parse_front_matter_text(text: str) -> dict:
    """YAML front matter를 간단히 파싱합니다."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    fm = {}
    current_key = None
    list_items = []

    for line in match.group(1).splitlines():
        # 리스트 항목
        if re.match(r"^\s+-\s+", line) and current_key:
            val = re.sub(r"^\s+-\s+", "", line).strip().strip('"').strip("'")
            list_items.append(val)
            fm[current_key] = list_items
            continue

        # 키-값
        kv = re.match(r"^(\w[\w.]*)\s*:\s*(.*)", line)
        if kv:
            current_key = kv.group(1)
            value = kv.group(2).strip().strip('"').strip("'")
            list_items = []
            if value:
                fm[current_key] = value
            continue

    return fm


def parse_front_matter(file_path: Path) -> dict:
    """파일의 YAML front matter를 파싱합니다."""
    return parse_front_matter_text(file_path.read_text(encoding="utf-8"))


def build_broadcast_html(meta: dict, post_url: str, lang: str) -> str:
    """포스트 메타데이터로 브로드캐스트 HTML을 생성합니다."""
    title = html_lib.escape(meta.get("title", "New Post"))
    description = html_lib.escape(meta.get("description", ""))
    tldr = html_lib.escape(meta.get("tldr", ""))
    escaped_post_url = html_lib.escape(post_url, quote=True)

    if lang == "ko":
        read_more = "계속 읽기"
        greeting = "새 글이 발행되었습니다."
    elif lang == "ja":
        read_more = "続きを読む"
        greeting = "新しい記事が公開されました。"
    else:
        read_more = "Read more"
        greeting = "A new post has been published."

    broadcast_html = f"""<h2>{title}</h2>
<p>{greeting}</p>
"""
    if tldr:
        broadcast_html += f"<p><strong>TL;DR:</strong> {tldr}</p>\n"
    elif description:
        broadcast_html += f"<p>{description}</p>\n"

    broadcast_html += f"""<p><a href="{escaped_post_url}">{read_more} →</a></p>
"""
    return broadcast_html


def request_json(req: urllib.request.Request) -> dict:
    """Kit API 요청을 실행하고 JSON 응답을 반환합니다."""
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ Kit API error {e.code}: {body}", file=sys.stderr)
        raise
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"❌ Kit API request failed: {e}", file=sys.stderr)
        raise


def broadcast_exists(api_key: str, subject: str) -> bool:
    """최근 브로드캐스트에 같은 제목이 있는지 확인합니다."""
    req = urllib.request.Request(
        API_URL,
        headers={"X-Kit-Api-Key": api_key},
        method="GET",
    )
    result = request_json(req)
    return any(item.get("subject") == subject for item in result.get("broadcasts", []))


def create_broadcast(api_key: str, subject: str, content: str,
                     description: str, send_at: str | None = None) -> dict:
    """Kit API v4를 호출하여 브로드캐스트를 생성합니다."""
    payload = {
        "subject": subject,
        "content": content,
        "description": description,
        "public": True,
        "published_at": send_at or datetime.now(timezone.utc).isoformat(),
        "send_at": send_at,
        "preview_text": description[:150] if description else "",
        "subscriber_filter": [],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Kit-Api-Key": api_key,
        },
        method="POST",
    )

    result = request_json(req)
    broadcast_id = result.get("broadcast", {}).get("id", "unknown")
    print(f"✅ Broadcast created: id={broadcast_id}")
    if send_at:
        print(f"   Scheduled for: {send_at}")
    else:
        print("   Saved as draft (no send_at provided)")
    return result


def find_new_posts(changed_files: str, lang: str = "ko") -> list[Path]:
    """변경된 파일 목록에서 새 포스트를 찾습니다."""
    posts = []
    for f in changed_files.strip().splitlines():
        f = f.strip()
        # content/{lang}/posts/*/index.md 패턴 매치
        if re.match(rf"^content/{lang}/posts/.+/index\.md$", f):
            path = Path(f)
            if path.exists():
                posts.append(path)
    return posts


def main():
    api_key = os.environ.get("KIT_API_KEY")
    if not api_key:
        print("❌ KIT_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    changed_files = os.environ.get("CHANGED_FILES", "")
    if not changed_files:
        print("ℹ️  No changed files provided. Nothing to do.")
        sys.exit(0)

    base_url = os.environ.get("BASE_URL", "https://devwrite.ai").rstrip("/")
    default_lang = os.environ.get("DEFAULT_LANG", "ko")
    send_at = os.environ.get("KIT_SEND_AT") or None

    posts = find_new_posts(changed_files, default_lang)
    if not posts:
        print("ℹ️  No new posts detected. Nothing to do.")
        sys.exit(0)

    print(f"📬 Found {len(posts)} new post(s) to broadcast")

    for post_path in posts:
        meta = parse_front_matter(post_path)
        if meta.get("draft", "false").lower() == "true":
            print(f"   Skipping draft: {post_path}")
            continue

        slug = meta.get("slug", post_path.parent.name)
        title = meta.get("title", slug)
        description = meta.get("description", "")

        post_url = f"{base_url}/{default_lang}/posts/{slug}/"
        subject = f"[/dev/write] {title}"
        content = build_broadcast_html(meta, post_url, default_lang)

        if broadcast_exists(api_key, subject):
            print(f"   Skipping existing broadcast: {subject}")
            continue

        print(f"   → Creating broadcast for: {title}")
        create_broadcast(api_key, subject, content, description, send_at)


if __name__ == "__main__":
    main()
