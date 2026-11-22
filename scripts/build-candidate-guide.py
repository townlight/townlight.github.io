"""Build the Windows 1.9.2.1 guide's HTML, Word and tagged PDF editions."""
from __future__ import annotations

import html
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuals/windows-1.9.2.1-candidate.md"
HTML = ROOT / "manuals/windows-1.9.2.1-candidate.html"
DOCX = ROOT / "docx/Townlight-Windows-1.9.2.1-Candidate.docx"
PDF = ROOT / "pdf/Townlight-Windows-1.9.2.1-Candidate.pdf"
WORD_REFERENCE = ROOT / "assets/word-reference.docx"
TITLE = "Townlight Windows 1.9.2.1 signed public beta guide"
RELEASE_URL = "https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.2.1"
MSI_URL = "https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/Townlight-Windows-x64-1.9.2.1.msi"
ACCEPTANCE_URL = "https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/ACCEPTANCE-Windows-1.9.2.1.md"
CHECKSUMS_URL = "https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/SHA256SUMS-Windows-1.9.2.1.txt"


def run(arguments: list[str]) -> None:
    result = subprocess.run(arguments, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"Documentation command failed ({result.returncode}): {arguments[0]}\n"
            f"{result.stdout}{result.stderr}"
        )


def build_html(pandoc: str) -> None:
    rendered = subprocess.check_output(
        [pandoc, str(SOURCE), "-f", "markdown+raw_html", "-t", "html5",
         "--toc", "--toc-depth=2", "--standalone", "-M", "pagetitle=" + TITLE],
        text=True,
    ).replace("\r\n", "\n")
    legacy_toc_ids = {
        'toc-townlight-windows-1.9.2.1-signed-public-beta': 'toc-windows-1.9.2.1-signed-candidate',
        'toc-what-windows-1.9.2.1-adds': 'toc-what-the-candidate-adds',
        'toc-source-pins-and-implementation': 'toc-setup-and-technical-references',
    }
    for generated_id, legacy_id in legacy_toc_ids.items():
        marker = f'id="{generated_id}"'
        if marker not in rendered:
            raise RuntimeError(f"Pandoc did not render the expected guide TOC id: {generated_id}")
        rendered = rendered.replace(marker, f'id="{legacy_id}"', 1)
    match = re.search(r"<body[^>]*>(.*?)</body>", rendered, re.S)
    if not match:
        raise RuntimeError("Pandoc did not render a document body")
    body = match.group(1)
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Windows 1.9.2.1 signed public beta guide, acceptance scope and release links.">
<title>{html.escape(TITLE)} | Townlight</title>
<link rel="stylesheet" href="../assets/site.css">
<link rel="icon" href="../brand/favicon.svg" type="image/svg+xml">
<link rel="icon" href="../brand/favicon.ico" sizes="16x16 32x32 48x48">
<link rel="apple-touch-icon" href="../brand/png/townlight-hall-app-icon-180.png">
</head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="../index.html"><img src="../brand/svg/townlight-hall-lockup.svg" alt="Townlight" width="217" height="45"></a>
<span class="edition">Release guide · Windows 1.9.2.1</span>
<nav aria-label="Main"><a href="../index.html#products">Products</a><a href="suite.html">Suite manual</a>
<a href="../reference/index.html">Technical reference</a><a href="../versions.html">Versions and release</a></nav></header>
<main id="main" class="reading wrap"><p class="edition">Windows 1.9.2.1 signed public beta</p>
<p class="docmeta"><a href="../pdf/{PDF.name}">Printable PDF</a> · <a href="../docx/{DOCX.name}">Editable Word</a></p>
<p class="docmeta"><a href="{MSI_URL}">Download signed MSI</a> · <a href="{RELEASE_URL}">Release catalog and source</a> · <a href="{CHECKSUMS_URL}">SHA-256 checksums</a> · <a href="{ACCEPTANCE_URL}">Acceptance and limits</a></p>
<article class="docbody">{body}</article></main>
<aside class="release-note" aria-label="Current release"><p><strong>Current release:</strong> Townlight for Windows 1.9.2.1. The acceptance used synthetic data on a physical Windows host and clean Sandbox guest on the same machine; direct upgrades were not tested. <a href="{MSI_URL}">Download MSI</a> · <a href="{RELEASE_URL}">Release catalog</a> · <a href="{ACCEPTANCE_URL}">Acceptance</a></p></aside>
<footer>Townlight · Acceptance evidence applies only to its identified artifacts.<span><a href="../announcement.html">Announcement</a> · <a href="../support.html">Support</a></span></footer>
</body></html>'''
    HTML.write_text(document, encoding="utf-8", newline="\n")


def build_word_and_pdf(pandoc: str) -> None:
    DOCX.parent.mkdir(parents=True, exist_ok=True)
    PDF.parent.mkdir(parents=True, exist_ok=True)
    run([pandoc, str(SOURCE), "-f", "markdown+raw_html", "--standalone", "--toc",
         "--reference-doc", str(WORD_REFERENCE), "-M", "title=" + TITLE,
         "-M", "subtitle=Signed public beta release guide", "-o", str(DOCX)])
    soffice = shutil.which("soffice.com") or shutil.which("soffice")
    if not soffice:
        installed = Path("C:/Program Files/LibreOffice/program/soffice.com")
        if installed.is_file():
            soffice = str(installed)
    if not soffice:
        raise RuntimeError("LibreOffice soffice.com is required for PDF conversion")
    with tempfile.TemporaryDirectory(prefix="townlight-release-docs-") as temporary:
        folder = Path(temporary)
        output = folder / "rendered"
        output.mkdir()
        profile = folder / "libreoffice-profile"
        run([soffice, "-env:UserInstallation=" + profile.as_uri(), "--headless",
             "--convert-to",
             'pdf:writer_pdf_Export:{"UseTaggedPDF":{"type":"boolean","value":"true"}}',
             "--outdir", str(output), str(DOCX)])
        rendered_pdf = output / (DOCX.stem + ".pdf")
        if not rendered_pdf.is_file() or not rendered_pdf.stat().st_size:
            raise RuntimeError("LibreOffice did not produce a non-empty PDF")
        shutil.copyfile(rendered_pdf, PDF)


def main() -> None:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("Pandoc is required to build the Windows release guide")
    if not SOURCE.is_file() or not WORD_REFERENCE.is_file():
        raise RuntimeError("Release Markdown source or Word reference template is missing")
    build_html(pandoc)
    build_word_and_pdf(pandoc)
    for path in (HTML, DOCX, PDF):
        print(f"Built {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
