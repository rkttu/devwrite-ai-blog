import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from scripts.sync_mcp_config import (
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE,
    build_portable_config,
    sync_config,
)


class McpConfigRenderingTests(unittest.TestCase):
    def test_converts_remote_http_server(self):
        config = {
            "mcp_servers": {
                "microsoft-learn": {
                    "url": "https://learn.microsoft.com/api/mcp"
                }
            }
        }

        portable = build_portable_config(config)

        self.assertEqual(
            portable,
            {
                "mcpServers": {
                    "microsoft-learn": {
                        "type": "http",
                        "url": "https://learn.microsoft.com/api/mcp",
                    }
                }
            },
        )

    def test_converts_stdio_server_without_client_specific_type(self):
        config = {
            "mcp_servers": {
                "example": {
                    "command": "npx",
                    "args": ["-y", "example-mcp"],
                    "env": {"MODE": "readonly"},
                }
            }
        }

        portable = build_portable_config(config)

        self.assertEqual(
            portable["mcpServers"]["example"],
            {
                "command": "npx",
                "args": ["-y", "example-mcp"],
                "env": {"MODE": "readonly"},
            },
        )

    def test_rejects_codex_only_fields_instead_of_dropping_them(self):
        config = {
            "mcp_servers": {
                "example": {
                    "url": "https://example.com/mcp",
                    "enabled_tools": ["search"],
                }
            }
        }

        with self.assertRaisesRegex(ValueError, "enabled_tools"):
            build_portable_config(config)

    def test_check_detects_outdated_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "config.toml"
            output = root / ".mcp.json"
            source.write_text(
                '[mcp_servers.example]\nurl = "https://example.com/mcp"\n',
                encoding="utf-8",
            )
            output.write_text("{}\n", encoding="utf-8")

            with redirect_stderr(io.StringIO()):
                self.assertFalse(sync_config(source, output, check=True))


class TrackedMcpConfigTests(unittest.TestCase):
    def test_shared_config_matches_codex_source(self):
        self.assertTrue(sync_config(DEFAULT_SOURCE, DEFAULT_OUTPUT, check=True))


if __name__ == "__main__":
    unittest.main()
