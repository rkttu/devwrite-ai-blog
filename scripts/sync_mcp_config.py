#!/usr/bin/env python3
"""Generate the portable MCP configuration from Codex project settings."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPOSITORY_ROOT / ".codex" / "config.toml"
DEFAULT_OUTPUT = REPOSITORY_ROOT / ".mcp.json"
SERVER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
REMOTE_FIELDS = {"url"}
STDIO_FIELDS = {"command", "args", "env", "cwd"}
CONTROL_FIELDS = {"enabled"}


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as source:
        return tomllib.load(source)


def _require_string(value: Any, field: str, server_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{server_name}.{field} 값은 비어 있지 않은 문자열이어야 합니다.")
    return value


def _render_remote_server(server_name: str, config: dict[str, Any]) -> dict[str, Any]:
    unsupported = set(config) - REMOTE_FIELDS - CONTROL_FIELDS
    if unsupported:
        names = ", ".join(sorted(unsupported))
        raise ValueError(
            f"{server_name}의 Codex 전용 필드를 공용 형식으로 변환할 수 없습니다: {names}"
        )

    return {
        "type": "http",
        "url": _require_string(config["url"], "url", server_name),
    }


def _render_stdio_server(server_name: str, config: dict[str, Any]) -> dict[str, Any]:
    unsupported = set(config) - STDIO_FIELDS - CONTROL_FIELDS
    if unsupported:
        names = ", ".join(sorted(unsupported))
        raise ValueError(
            f"{server_name}의 Codex 전용 필드를 공용 형식으로 변환할 수 없습니다: {names}"
        )

    rendered: dict[str, Any] = {
        "command": _require_string(config["command"], "command", server_name)
    }

    args = config.get("args")
    if args is not None:
        if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
            raise ValueError(f"{server_name}.args 값은 문자열 배열이어야 합니다.")
        rendered["args"] = args

    env = config.get("env")
    if env is not None:
        if not isinstance(env, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in env.items()
        ):
            raise ValueError(f"{server_name}.env 값은 문자열 키와 값으로 구성해야 합니다.")
        rendered["env"] = env

    cwd = config.get("cwd")
    if cwd is not None:
        rendered["cwd"] = _require_string(cwd, "cwd", server_name)

    return rendered


def build_portable_config(config: dict[str, Any]) -> dict[str, Any]:
    servers = config.get("mcp_servers")
    if not isinstance(servers, dict) or not servers:
        raise ValueError("mcp_servers 테이블에 서버를 하나 이상 정의해야 합니다.")

    portable_servers: dict[str, Any] = {}
    for server_name, server_config in sorted(servers.items()):
        if not isinstance(server_name, str) or not SERVER_NAME_PATTERN.fullmatch(server_name):
            raise ValueError(
                "서버 이름에는 영문자, 숫자, 하이픈, 밑줄만 사용할 수 있습니다: "
                f"{server_name}"
            )
        if not isinstance(server_config, dict):
            raise ValueError(f"{server_name} 설정은 TOML 테이블이어야 합니다.")

        enabled = server_config.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(f"{server_name}.enabled 값은 불리언이어야 합니다.")
        if not enabled:
            continue

        has_url = "url" in server_config
        has_command = "command" in server_config
        if has_url == has_command:
            raise ValueError(
                f"{server_name}에는 url 또는 command 중 하나만 정의해야 합니다."
            )

        if has_url:
            portable_servers[server_name] = _render_remote_server(
                server_name, server_config
            )
        else:
            portable_servers[server_name] = _render_stdio_server(
                server_name, server_config
            )

    return {"mcpServers": portable_servers}


def render_portable_config(config: dict[str, Any]) -> str:
    return json.dumps(
        build_portable_config(config), ensure_ascii=False, indent=2
    ) + "\n"


def sync_config(source: Path, output: Path, check: bool = False) -> bool:
    rendered = render_portable_config(load_toml(source))
    if check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            print(
                f"{output} 파일이 {source} 원본과 일치하지 않습니다. "
                "python3 scripts/sync_mcp_config.py를 실행하십시오.",
                file=sys.stderr,
            )
            return False
        return True

    output.write_text(rendered, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Codex 프로젝트 설정에서 공용 .mcp.json을 생성합니다."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="생성하지 않고 기존 출력이 원본과 일치하는지 검사합니다.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return 0 if sync_config(args.source, args.output, args.check) else 1
    except (OSError, tomllib.TOMLDecodeError, ValueError) as error:
        print(f"MCP 설정 동기화 실패: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
