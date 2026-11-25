"""Build community-module Markdown, HTML, Word and tagged PDF editions."""

from __future__ import annotations

import argparse
import html
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from community_diagrams import prepare_diagrams

ROOT = Path(__file__).resolve().parents[1]
MANUALS = ROOT / "manuals"
DOCX_DIR = ROOT / "docx"
PDF_DIR = ROOT / "pdf"
WORD_REFERENCE = ROOT / "assets/word-reference.docx"
EXPORTER = ROOT / "scripts/export-owner-manuals.py"

ENTRIES = (
    (Path("311/USER-MANUAL.md"), "311", "Townlight-311-Manual-Beta-1",
     "Townlight 311 Manual Beta 1", "Windows 1.10.0.1 source candidate, installed acceptance pending", "Windows 1.10.0.1 source candidate, installed acceptance pending"),
    (Path("comms/USER-MANUAL.md"), "communications", "Townlight-Communications-Manual-Beta-1",
     "Townlight Communications Manual Beta 1", "Windows 1.10.0.1 source candidate, installed acceptance pending", "Windows 1.10.0.1 source candidate, installed acceptance pending"),
    (Path("parks/USER-MANUAL.md"), "parks", "Townlight-Parks-Manual-Beta-1",
     "Townlight Parks Manual Beta 1", "Windows 1.10.0.1 source candidate, installed acceptance pending", "Windows 1.10.0.1 source candidate, installed acceptance pending"),
    (Path("suite/docs/windows-311-communications-parks.md"),
     "windows-community-modules-candidate",
     "Townlight-Windows-Community-Modules-Candidate",
     "Townlight Windows Community Modules Candidate",
     "Windows community modules candidate",
     "Windows 1.10.0.1 source candidate"),
)

NOTICE = (
    "Unpublished Windows 1.10.0.1 source candidate; acceptance pending. "
    "Public release 1.9.3.2 is unchanged; no public candidate MSI URL exists."
)


def run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(
            f"Documentation command failed ({result.returncode}): {arguments[0]}\n"
            f"{result.stdout}{result.stderr}"
        )
    return result


def render_html(pandoc: str, source: Path, title: str, edition: str,
                slug: str, docx_name: str, pdf_name: str,
                resource_parent: Path | None = None) -> Path:
    result = run([
        pandoc, str(source), "-f", "markdown+raw_html", "-t", "html5",
        "--toc", "--toc-depth=2", "--standalone", "-M", "pagetitle=" + title,
        "--resource-path", str(resource_parent or source.parent),
    ])
    if not result.stdout.strip():
        raise RuntimeError(f"Pandoc returned empty HTML for {source}")
    match = re.search(r"<body[^>]*>(.*?)</body>", result.stdout, re.S)
    if not match:
        raise RuntimeError(f"Pandoc did not render a document body for {source}")
    body = match.group(1)
    destination = MANUALS / f"{slug}.html"
    destination.write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | Townlight</title>
<link rel="stylesheet" href="../assets/site.css">
<link rel="icon" href="../brand/favicon.svg" type="image/svg+xml">
<link rel="icon" href="../brand/favicon.ico" sizes="16x16 32x32 48x48">
<link rel="apple-touch-icon" href="../brand/png/townlight-hall-app-icon-180.png">
</head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="../index.html"><img src="../brand/svg/townlight-hall-lockup.svg" alt="Townlight" width="217" height="45"></a>
<span class="edition">{html.escape(edition)}</span>
<nav aria-label="Main"><a href="../index.html#products">Products</a><a href="suite.html">Suite manual</a>
<a href="../reference/index.html">Technical reference</a><a href="../versions.html">Versions and release</a></nav></header>
<main id="main" class="reading wrap"><p class="edition">{html.escape(edition)}</p>
<p class="docmeta"><a href="../pdf/{pdf_name}">Printable PDF</a> · <a href="../docx/{docx_name}">Editable Word</a></p>
<aside class="release-note" aria-label="Release notice"><p><strong>Notice:</strong> {html.escape(NOTICE)}</p></aside>
<article class="docbody">{body}</article></main>
<footer>Townlight · Acceptance evidence applies only to its identified artifacts.<span><a href="../announcement.html">Announcement</a> · <a href="../support.html">Support</a></span></footer>
</body></html>''', encoding="utf-8", newline="\n")
    if not destination.is_file() or not destination.stat().st_size:
        raise RuntimeError(f"HTML output is empty: {destination}")
    return destination


def render_docx(pandoc: str, source: Path, title: str, subtitle: str,
                destination: Path, resource_parent: Path | None = None) -> Path:
    run([
        pandoc, str(source), "-f", "markdown+raw_html", "--standalone", "--toc",
        "--resource-path", str(resource_parent or source.parent), "--reference-doc", str(WORD_REFERENCE),
        "-M", "title=" + title, "-M", "subtitle=" + subtitle, "-o", str(destination),
    ])
    if not destination.is_file() or not destination.stat().st_size:
        raise RuntimeError(f"Word output is empty: {destination}")
    return destination


def load_pdf_renderer():
    spec = importlib.util.spec_from_file_location("townlight_export_owner_manuals", EXPORTER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load existing exporter: {EXPORTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    renderer = getattr(module, "render_tagged_pdfs", None)
    if not callable(renderer):
        raise RuntimeError(f"render_tagged_pdfs is unavailable in {EXPORTER}")
    return renderer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path,
                        help="Parent containing suite/, 311/, comms/ and parks/")
    parser.add_argument("--mermaid-cli", default=shutil.which("mmdc"),
                        help="Mermaid CLI executable or .js path (default: mmdc on PATH)")
    parser.add_argument("--mermaid-browser", default=None,
                        help="Optional browser executable for Mermaid CLI")
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if not source_root.is_dir():
        raise SystemExit(f"Source root is not a directory: {source_root}")
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("Pandoc is required")
    if not args.mermaid_cli:
        raise RuntimeError("Mermaid CLI is required; install mmdc or pass --mermaid-cli")
    if not WORD_REFERENCE.is_file():
        raise RuntimeError(f"Word reference template is missing: {WORD_REFERENCE}")
    for folder in (MANUALS, DOCX_DIR, PDF_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    docx_paths: list[Path] = []
    built: list[Path] = []
    for relative, slug, stem, title, subtitle, edition in ENTRIES:
        source = source_root / relative
        if not source.is_file():
            raise RuntimeError(f"Input Markdown is missing: {source}")
        markdown = MANUALS / f"{slug}.md"
        if source.resolve() != markdown.resolve():
            shutil.copyfile(source, markdown)
        if not markdown.is_file() or not markdown.stat().st_size:
            raise RuntimeError(f"Markdown output is empty: {markdown}")
        docx_path = DOCX_DIR / f"{stem}.docx"
        pdf_name = f"{stem}.pdf"
        with tempfile.TemporaryDirectory() as temporary_name:
            temporary = Path(temporary_name)
            html_markdown, word_markdown, images = prepare_diagrams(
                source.read_text(encoding="utf-8"), slug,
                ROOT / "assets/diagrams/community", temporary,
                args.mermaid_cli, args.mermaid_browser,
            )
            for prepared in (html_markdown, word_markdown):
                if re.search(r"(?m)^```\s*mermaid\b", prepared):
                    raise RuntimeError(
                        f"Unclosed Mermaid fence remains in prepared Markdown for {source}"
                    )
            html_source = temporary / "prepared-html.md"
            word_source = temporary / "prepared-word.md"
            html_source.write_text(html_markdown, encoding="utf-8", newline="\n")
            word_source.write_text(word_markdown, encoding="utf-8", newline="\n")
            html_path = render_html(pandoc, html_source, title, edition, slug,
                                    docx_path.name, pdf_name,
                                    resource_parent=source.parent)
            render_docx(pandoc, word_source, title, subtitle, docx_path,
                        resource_parent=source.parent)
        docx_paths.append(docx_path)
        built.append(markdown)
        built.append(html_path)
        built.append(docx_path)
        built.extend(images)

    load_pdf_renderer()(docx_paths)
    for docx_path in docx_paths:
        pdf_path = PDF_DIR / f"{docx_path.stem}.pdf"
        if not pdf_path.is_file() or not pdf_path.stat().st_size:
            raise RuntimeError(f"PDF output is empty: {pdf_path}")
        built.append(pdf_path)
    for path in built:
        print(f"Built {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
