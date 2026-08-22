#!/usr/bin/env python3
"""Hugo 운영 산출물의 링크와 구조화 데이터를 검증합니다."""

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


SITE_HOST = "devwrite.ai"
REQUIRED_FILES = {
    "404.html",
    "apple-touch-icon.png",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "favicon.ico",
    "llms.txt",
    "robots.txt",
    "sitemap.xml",
}


class DocumentParser(HTMLParser):
    def __init__(self, path: Path):
        super().__init__()
        self.path = path
        self.references: list[str] = []
        self.json_documents: list[dict] = []
        self.json_errors: list[str] = []
        self.image_errors: list[str] = []
        self._in_json = False
        self._json_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {"a", "link"} and attributes.get("href"):
            self.references.append(attributes["href"] or "")
        if tag in {"img", "script"} and attributes.get("src"):
            self.references.append(attributes["src"] or "")
        if tag == "img" and not attributes.get("alt"):
            self.image_errors.append(f"{self.path}: alt가 없는 이미지")
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self._in_json = True
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self._in_json:
            self._json_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "script" or not self._in_json:
            return
        try:
            self.json_documents.append(json.loads("".join(self._json_buffer)))
        except json.JSONDecodeError as error:
            self.json_errors.append(f"{self.path}: JSON-LD 파싱 실패: {error}")
        self._in_json = False


def iter_schema_nodes(value):
    if isinstance(value, dict):
        if "@type" in value:
            yield value
        for item in value.values():
            yield from iter_schema_nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_schema_nodes(item)


def resolve_reference(root: Path, document: Path, reference: str) -> Path | None:
    parsed = urlparse(reference)
    if parsed.scheme and parsed.hostname != SITE_HOST:
        return None
    if reference.startswith(("#", "mailto:", "tel:", "data:", "//")):
        return None

    path = unquote(parsed.path)
    if not path:
        return None
    target = root / path.lstrip("/") if path.startswith("/") else document.parent / path
    if target.is_dir():
        target /= "index.html"
    elif not target.suffix:
        target /= "index.html"
    return target


def validate(public_dir: Path) -> list[str]:
    errors: list[str] = []
    missing_required = sorted(name for name in REQUIRED_FILES if not (public_dir / name).is_file())
    errors.extend(f"필수 산출물 누락: {name}" for name in missing_required)

    json_count = 0
    for html_file in public_dir.rglob("*.html"):
        relative = html_file.relative_to(public_dir)
        text = html_file.read_text(encoding="utf-8", errors="replace")
        parser = DocumentParser(relative)
        parser.feed(text)
        errors.extend(parser.json_errors)
        errors.extend(parser.image_errors)
        json_count += len(parser.json_documents)

        for reference in parser.references:
            target = resolve_reference(public_dir, html_file, reference)
            if target is not None and not target.exists():
                errors.append(f"{relative}: 존재하지 않는 내부 참조: {reference}")

        schema_types = {
            node.get("@type")
            for document in parser.json_documents
            for node in iter_schema_nodes(document)
        }
        if relative.parts[-2:] in [("search", "index.html"), ("archives", "index.html")]:
            if "BlogPosting" in schema_types:
                errors.append(f"{relative}: 목록 페이지를 BlogPosting으로 선언함")
        if "0001-01-01" in text:
            errors.append(f"{relative}: 초기값 날짜가 출력됨")

    root_404 = public_dir / "404.html"
    if root_404.is_file():
        text = root_404.read_text(encoding="utf-8", errors="replace")
        if 'content="noindex, nofollow"' not in text:
            errors.append("404.html: noindex 정책 누락")
        for language in ("ko", "en", "ja"):
            if f"data-lang={language}" not in text and f'data-lang="{language}"' not in text:
                errors.append(f"404.html: {language} 최근 글 영역 누락")

    if json_count == 0:
        errors.append("JSON-LD 문서가 생성되지 않음")
    return sorted(set(errors))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public_dir", type=Path, nargs="?", default=Path("public"))
    args = parser.parse_args()

    errors = validate(args.public_dir.resolve())
    if errors:
        print(f"사이트 검증 실패: {len(errors)}건")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("사이트 산출물 검증을 통과했습니다.")


if __name__ == "__main__":
    main()
