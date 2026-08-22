#!/usr/bin/env python3
"""Git 변경 범위에서 새로 발행된 한국어 포스트를 찾습니다."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

if __package__:
    from .kit_broadcast import parse_front_matter_text
else:
    from kit_broadcast import parse_front_matter_text


PROJECT_ROOT = Path(__file__).resolve().parent.parent
POST_PATH_PATTERN = re.compile(
    r"^content/ko/posts/[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*/index\.md$"
)
ZERO_SHA = "0" * 40


def run_git(*args: str, check: bool = True) -> str:
    """프로젝트 루트에서 Git 명령을 실행합니다."""
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def validate_post_path(path: str) -> Path:
    """워크플로 입력 경로를 허용된 포스트 경로로 제한합니다."""
    if not POST_PATH_PATTERN.fullmatch(path):
        raise ValueError(f"허용되지 않은 포스트 경로입니다: {path}")

    resolved = (PROJECT_ROOT / path).resolve()
    posts_root = (PROJECT_ROOT / "content" / "ko" / "posts").resolve()
    if posts_root not in resolved.parents or not resolved.is_file():
        raise ValueError(f"포스트 파일을 찾을 수 없습니다: {path}")
    return resolved


def read_revision_file(revision: str, path: str) -> str | None:
    """특정 리비전의 파일 내용을 읽습니다."""
    if not revision or revision == ZERO_SHA:
        return None
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=PROJECT_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout if result.returncode == 0 else None


def is_published(text: str | None) -> bool:
    """front matter의 draft 값으로 발행 상태를 판정합니다."""
    if text is None:
        return False
    draft = str(parse_front_matter_text(text).get("draft", "false")).lower()
    return draft != "true"


def changed_post_paths(before: str, after: str) -> list[str]:
    """두 리비전 사이에서 추가되거나 수정된 포스트 경로를 반환합니다."""
    if before == ZERO_SHA:
        output = run_git("ls-tree", "-r", "--name-only", after, "content/ko/posts")
    else:
        output = run_git(
            "diff", "--name-only", "--diff-filter=AM", before, after,
            "--", "content/ko/posts/*/index.md",
        )
    return sorted({line.strip() for line in output.splitlines() if line.strip()})


def detect_newly_published(before: str, after: str) -> list[str]:
    """추가 발행 또는 draft 해제에 해당하는 포스트를 반환합니다."""
    published = []
    for path in changed_post_paths(before, after):
        if not POST_PATH_PATTERN.fullmatch(path):
            continue
        old_text = read_revision_file(before, path)
        new_text = read_revision_file(after, path)
        if not is_published(old_text) and is_published(new_text):
            published.append(path)
    return published


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before")
    parser.add_argument("--after")
    parser.add_argument("--post-path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        if args.post_path:
            post_path = validate_post_path(args.post_path)
            relative = post_path.relative_to(PROJECT_ROOT).as_posix()
            if not is_published(post_path.read_text(encoding="utf-8")):
                raise ValueError(f"드래프트 포스트는 발송할 수 없습니다: {relative}")
            posts = [relative]
        else:
            if not args.before or not args.after:
                raise ValueError("자동 감지에는 --before와 --after가 필요합니다.")
            posts = detect_newly_published(args.before, args.after)
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"오류: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    Path(args.output).write_text("\n".join(posts) + ("\n" if posts else ""), encoding="utf-8")
    for post in posts:
        print(post)


if __name__ == "__main__":
    main()
