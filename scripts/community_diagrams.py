import json
import re
import shutil
import struct
import subprocess
from pathlib import Path

_MERMAID = re.compile(r"^\s*```mermaid\s*$")
_FENCE = re.compile(r"^\s*```")
_CLOSING = re.compile(r"^\s*```\s*$")
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")


def _escape_alt(text: str) -> str:
    return text.replace("[", r"\[").replace("]", r"\]")


def _caption(heading: str, ordinal: int) -> str:
    heading = heading.strip()
    return f"{heading} — diagram {ordinal}" if heading else f"Diagram {ordinal}"


def _write(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        head = fh.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"Invalid PNG output: {path}")
    width, height = struct.unpack(">II", head[16:24])
    if width == 0 or height == 0:
        raise RuntimeError(f"Invalid PNG dimensions: {path}")
    return width, height


def _render(
    mmd: Path,
    svg: Path,
    png: Path,
    temporary: Path,
    stem: str,
    cli: str,
    browser: str | None,
) -> tuple[Path, Path]:
    for out in (svg, png):
        try:
            out.unlink()
        except FileNotFoundError:
            pass

    config = {
        "theme": "neutral",
        "fontFamily": "Arial",
        "flowchart": {"htmlLabels": False, "wrappingWidth": 180},
        "sequence": {
            "wrap": True,
            "width": 130,
            "actorMargin": 20,
            "messageMargin": 30,
        },
    }
    config_path = temporary / f"{stem}-mermaid-config.json"
    _write(config_path, json.dumps(config))

    browser_path = None
    if browser:
        browser_path = temporary / f"{stem}-browser-config.json"
        _write(browser_path, json.dumps({"executablePath": browser}))

    base = [shutil.which("node") or "node", cli] if cli.endswith(".js") else [cli]
    for out in (svg, png):
        args = base + [
            "-i", str(mmd),
            "-o", str(out),
            "-b", "white",
            "-s", "2",
            "-c", str(config_path),
        ]
        if browser_path:
            args += ["-p", str(browser_path)]
        try:
            subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120,
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or str(exc)).strip()
            raise RuntimeError(f"Mermaid render failed for {out.name}: {detail}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Mermaid render timed out for {out.name}") from exc
        except OSError as exc:
            raise RuntimeError(f"Could not run Mermaid CLI for {out.name}: {exc}") from exc

        if not out.is_file() or out.stat().st_size == 0:
            raise RuntimeError(f"Mermaid did not produce a nonempty {out.name}")

    return svg, png


def prepare_diagrams(
    markdown: str,
    slug: str,
    assets: Path,
    temporary: Path,
    cli: str,
    browser: str | None,
) -> tuple[str, str, list[Path]]:
    lines = markdown.splitlines(keepends=True)
    html_out: list[str] = []
    word_out: list[str] = []
    generated: list[Path] = []
    heading = ""
    ordinal = 0
    in_other_fence = False
    i = 0

    while i < len(lines):
        line = lines[i]
        noeol = line.rstrip("\r\n")
        eol = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""

        if in_other_fence:
            html_out.append(line)
            word_out.append(line)
            if _CLOSING.match(noeol):
                in_other_fence = False
            i += 1
            continue

        match = _HEADING.match(noeol)
        if match:
            heading = match.group(2).strip()

        if _MERMAID.match(noeol):
            j = i + 1
            block: list[str] = []
            while j < len(lines) and not _CLOSING.match(lines[j].rstrip("\r\n")):
                block.append(lines[j])
                j += 1
            if j >= len(lines):
                html_out.extend(lines[i:])
                word_out.extend(lines[i:])
                break

            ordinal += 1
            stem = f"{slug}-{ordinal}"
            assets.mkdir(parents=True, exist_ok=True)
            mmd = temporary / f"{stem}.mmd"
            _write(mmd, "".join(block))
            svg_path = assets / f"{stem}.svg"
            png_path = assets / f"{stem}.png"
            _render(mmd, svg_path, png_path, temporary, stem, cli, browser)
            generated.extend([svg_path, png_path])

            caption = _escape_alt(_caption(heading, ordinal))
            html_src = f"../assets/diagrams/community/{stem}.svg"
            html_out.append(f"![{caption}]({html_src}){eol}")

            png_w, png_h = _png_size(png_path)
            width_in = min(6.3, 7.4 * png_w / png_h)
            word_src = f"<{png_path.resolve()}>"
            word_out.append(f"![{caption}]({word_src}){{width={width_in:.2f}in}}{eol}")

            i = j + 1
            continue

        if _FENCE.match(noeol):
            in_other_fence = True

        html_out.append(line)
        word_out.append(line)
        i += 1

    if ordinal == 0:
        return markdown, markdown, []
    return "".join(html_out), "".join(word_out), generated
