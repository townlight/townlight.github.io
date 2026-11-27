import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import community_diagrams


class CommunityDiagramsTest(unittest.TestCase):
    def _png(self, width: int, height: int) -> bytes:
        return (
            b"\x89PNG\r\n\x1a\n"
            + struct.pack(">I", 13)
            + b"IHDR"
            + struct.pack(">II", width, height)
        )

    def test_two_diagrams_crlf_links_alt_and_browser_config(self):
        md = (
            "# Intro\r\n\r\nBefore.\r\n\r\n## First\r\n\r\n"
            "```mermaid\r\ngraph TD; A-->B\r\n```\r\n\r\n"
            '```json\r\n{"note": "# Fake heading"}\r\n```\r\n\r\n'
            "## Second\r\n\r\n"
            "```mermaid\r\nsequenceDiagram\r\nA->>B: Hi\r\n```\r\n\r\nAfter.\r\n"
        )
        before = md
        node = shutil.which("node") or "node"
        cli = "mermaid-cli.js"
        browser = "/fake/chrome"
        png_dims = iter([(900, 600), (300, 600)])

        def fake_run(args, **kwargs):
            self.assertEqual(kwargs.get("check"), True)
            self.assertEqual(args[0], node)
            self.assertEqual(args[1], cli)
            if "-p" in args:
                cfg = Path(args[args.index("-p") + 1])
                self.assertTrue(cfg.is_file())
                self.assertEqual(
                    json.loads(cfg.read_text(encoding="utf-8"))["executablePath"],
                    browser,
                )
            out = Path(args[args.index("-o") + 1])
            if out.suffix == ".svg":
                out.write_bytes(b"<svg></svg>")
            else:
                out.write_bytes(self._png(*next(png_dims)))
            return subprocess.CompletedProcess(args, 0)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            assets = root / "assets"
            temporary = root / "work"
            temporary.mkdir()
            with mock.patch.object(
                community_diagrams.subprocess, "run", side_effect=fake_run
            ) as run_mock:
                html, word, generated = community_diagrams.prepare_diagrams(
                    md, "demo", assets, temporary, cli, browser
                )

            self.assertEqual(md, before)
            self.assertIn(
                "![First — diagram 1](../assets/diagrams/community/demo-1.svg)\r\n",
                html,
            )
            self.assertIn(
                "![Second — diagram 2](../assets/diagrams/community/demo-2.svg)\r\n",
                html,
            )
            self.assertIn(
                f"![First — diagram 1](<{(assets / 'demo-1.png').resolve()}>"
                "){width=6.30in}",
                word,
            )
            self.assertIn(
                f"![Second — diagram 2](<{(assets / 'demo-2.png').resolve()}>"
                "){width=3.70in}",
                word,
            )
            for text in (html, word):
                self.assertIn("Before.", text)
                self.assertIn("After.", text)
                self.assertIn("# Fake heading", text)
                self.assertNotIn("Fake heading — diagram", text)
            self.assertEqual(
                generated,
                [
                    assets / "demo-1.svg",
                    assets / "demo-1.png",
                    assets / "demo-2.svg",
                    assets / "demo-2.png",
                ],
            )
            self.assertEqual(run_mock.call_count, 4)
            for call in run_mock.call_args_list:
                args = call.args[0]
                self.assertEqual(args[0], node)
                self.assertEqual(args[1], cli)
                self.assertIn("-p", args)

    def test_renderer_failure_reports_stderr(self):
        md = "## Broken\n\n```mermaid\ngraph TD;\n```\n"
        error = subprocess.CalledProcessError(1, ["mermaid"], stderr="browser exploded")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            temporary = root / "work"
            temporary.mkdir()
            with mock.patch.object(
                community_diagrams.subprocess, "run", side_effect=error
            ):
                with self.assertRaises(RuntimeError) as ctx:
                    community_diagrams.prepare_diagrams(
                        md, "demo", root / "assets", temporary, "mermaid.js", None
                    )
            self.assertIn("Mermaid render failed", str(ctx.exception))
            self.assertIn("browser exploded", str(ctx.exception))

    def test_success_without_output_raises(self):
        md = "## Missing\n\n```mermaid\ngraph TD;\n```\n"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            temporary = root / "work"
            temporary.mkdir()
            with mock.patch.object(
                community_diagrams.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0),
            ):
                with self.assertRaises(RuntimeError) as ctx:
                    community_diagrams.prepare_diagrams(
                        md, "demo", root / "assets", temporary, "mermaid.js", None
                    )
            self.assertIn("nonempty", str(ctx.exception))

    def test_no_diagrams_is_unchanged_and_does_not_render(self):
        text = "Plain\r\ntext\r\n"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            temporary = root / "work"
            temporary.mkdir()
            with mock.patch.object(community_diagrams.subprocess, "run") as run_mock:
                html, word, generated = community_diagrams.prepare_diagrams(
                    text, "demo", root / "assets", temporary, "mermaid.js", None
                )
            run_mock.assert_not_called()
            self.assertEqual(html, text)
            self.assertEqual(word, text)
            self.assertEqual(generated, [])


if __name__ == "__main__":
    unittest.main()
