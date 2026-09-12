#!/usr/bin/env python3
"""Generate the Copilot/Claude instruction files from AGENTS.md (source of truth)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPOSITORY_ROOT / "AGENTS.md"

SYNC_BEGIN = "<!-- SYNC:BEGIN -->"
SYNC_END = "<!-- SYNC:END -->"

GENERATED_NOTICE = (
    "<!-- 이 파일은 AGENTS.md에서 자동 생성됩니다. 수정하려면 AGENTS.md를 고친 뒤 "
    "`python3 scripts/sync_agent_docs.py`를 실행하세요. -->"
)

COPILOT_HEADER = f"""# DevWrite Blog - Copilot Instructions

{GENERATED_NOTICE}

이 문서는 GitHub Copilot 및 AI 에이전트가 이 블로그 리포지토리에서 작업할 때 따라야 할 규칙입니다.
원본은 [AGENTS.md](../AGENTS.md)입니다.
"""

CLAUDE_HEADER = f"""# CLAUDE.md

{GENERATED_NOTICE}

이 파일은 Claude Code가 이 저장소에서 작업할 때 자동으로 컨텍스트에 로드됩니다.
원본은 [AGENTS.md](./AGENTS.md)입니다.

한국어 글쓰기 스타일 가이드는 다음 파일에서 불러옵니다.

@./writing-style-guide.md
"""

TARGETS = {
    REPOSITORY_ROOT / ".github" / "copilot-instructions.md": COPILOT_HEADER,
    REPOSITORY_ROOT / "CLAUDE.md": CLAUDE_HEADER,
}


def extract_shared_body(source_text: str) -> str:
    pattern = re.compile(
        re.escape(SYNC_BEGIN) + r"\n(.*)\n" + re.escape(SYNC_END), re.DOTALL
    )
    match = pattern.search(source_text)
    if not match:
        raise ValueError(
            f"{SOURCE}에서 {SYNC_BEGIN} ~ {SYNC_END} 구간을 찾을 수 없습니다."
        )
    return match.group(1).strip("\n")


def render_target(header: str, shared_body: str) -> str:
    return f"{header}\n{shared_body}\n"


def sync_docs(check: bool = False) -> bool:
    source_text = SOURCE.read_text(encoding="utf-8")
    shared_body = extract_shared_body(source_text)

    all_synced = True
    for target, header in TARGETS.items():
        rendered = render_target(header, shared_body)
        if check:
            if not target.is_file() or target.read_text(encoding="utf-8") != rendered:
                print(
                    f"{target} 파일이 AGENTS.md 원본과 일치하지 않습니다. "
                    "python3 scripts/sync_agent_docs.py를 실행하십시오.",
                    file=sys.stderr,
                )
                all_synced = False
            continue
        target.write_text(rendered, encoding="utf-8")

    return all_synced


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AGENTS.md에서 공용 Copilot/Claude 지침 파일을 생성합니다."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="생성하지 않고 기존 출력이 원본과 일치하는지 검사합니다.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return 0 if sync_docs(args.check) else 1
    except (OSError, ValueError) as error:
        print(f"에이전트 지침 동기화 실패: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
