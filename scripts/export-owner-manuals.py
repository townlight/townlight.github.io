"""Export the maintained owner Markdown manuals to the public site editions."""
from __future__ import annotations

import argparse
import html
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = {
    "suite": ("Townlight Suite", "Townlight-Suite-Manual-Beta-1"),
    "meetings": ("Townlight Meetings", "Townlight-Meetings-Manual-Beta-1"),
    "records": ("Townlight Records", "Townlight-Records-Manual-Beta-1"),
    "station": ("Townlight Station", "Townlight-Station-Manual-Beta-1"),
}


def run(arguments: list[str]) -> None:
    result = subprocess.run(arguments, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(
            f"Documentation command failed ({result.returncode}): {arguments[0]}\n"
            f"{result.stdout}{result.stderr}"
        )


def make_html(pandoc: str, source: Path, slug: str, title: str,
              file_stem: str, stylesheet: str) -> None:
    rendered = subprocess.check_output(
        [pandoc, str(source), "-f", "markdown+raw_html", "-t", "html5",
         "--standalone", "-M", "pagetitle=" + title], text=True, encoding="utf-8"
    ).replace("\r\n", "\n")
    match = re.search(r"<body[^>]*>(.*?)</body>", rendered, re.S)
    if not match:
        raise RuntimeError(f"Pandoc did not render a body for {source}")
    body = match.group(1)
    candidate_url = "https://townlight.github.io/manuals/windows-1.9.2.1-candidate.html"
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{html.escape(title)}; includes a scoped Windows 1.9.2.1 signed-candidate note.">
<title>{html.escape(title)} | Townlight</title>
<link rel="stylesheet" href="{stylesheet}">
<link rel="icon" href="../brand/favicon.svg" type="image/svg+xml">
<link rel="icon" href="../brand/favicon.ico" sizes="16x16 32x32 48x48">
<link rel="apple-touch-icon" href="../brand/png/townlight-hall-app-icon-180.png">
</head><body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="../index.html"><img src="../brand/svg/townlight-hall-lockup.svg" alt="Townlight" width="217" height="45"></a>
<span class="edition">Current manual · candidate note included</span>
<nav aria-label="Main"><a href="suite.html">Suite manual</a><a href="../reference/index.html">Technical reference</a>
<a href="../versions.html">Versions and Windows release</a></nav></header>
<main id="main" class="reading wrap"><p class="edition">Windows 1.9.2.1 signed candidate · not publicly distributed</p>
<p class="docmeta"><a href="../pdf/{file_stem}.pdf">Printable PDF</a> · <a href="../docx/{file_stem}.docx">Editable Word</a> · <a href="{candidate_url}">Candidate guide</a></p>
<article class="docbody">{body}</article></main>
<aside class="release-note" aria-label="Current release"><p><strong>Current Windows release:</strong> Townlight 1.9.1.1, a signed public beta. The 1.9.2.1 candidate has not been distributed. <a href="https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.1.1">1.9.1.1 release</a> · <a href="../versions.html">Versions and limits</a></p></aside>
<footer>Townlight · Candidate notes apply only to their identified artifacts.<span><a href="../announcement.html">Announcement</a> · <a href="../support.html">Support</a></span></footer>
</body></html>'''
    (ROOT / "manuals" / f"{slug}.html").write_text(document, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True, help="Owner USER-MANUAL.md")
    parser.add_argument("--meetings", type=Path, required=True, help="Owner USER-MANUAL.md")
    parser.add_argument("--records", type=Path, required=True, help="Owner USER-MANUAL.md")
    parser.add_argument("--station", type=Path, required=True, help="Station beta-1/USER-MANUAL.md")
    args = parser.parse_args()
    sources = {slug: getattr(args, slug).resolve() for slug in PRODUCTS}
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise RuntimeError("Manual source file(s) missing: " + ", ".join(missing))

    pandoc = shutil.which("pandoc")
    soffice = shutil.which("soffice.com") or shutil.which("soffice")
    if not soffice:
        installed = Path("C:/Program Files/LibreOffice/program/soffice.com")
        if installed.is_file():
            soffice = str(installed)
    reference = ROOT / "assets/word-reference.docx"
    if not pandoc or not soffice or not reference.is_file():
        raise RuntimeError("Pandoc, LibreOffice soffice.com, and assets/word-reference.docx are required")

    docx_paths: list[Path] = []
    for slug, (product, file_stem) in PRODUCTS.items():
        title = product + " Manual"
        source = sources[slug]
        make_html(pandoc, source, slug, title, file_stem, "../assets/site.css")
        docx = ROOT / "docx" / f"{file_stem}.docx"
        run([pandoc, str(source), "-f", "markdown+raw_html", "--standalone",
             "--reference-doc", str(reference), "-M", "title=" + title, "-o", str(docx)])
        docx_paths.append(docx)
        print(f"Rendered manuals/{slug}.html and {docx.relative_to(ROOT)} from {source}")

    with tempfile.TemporaryDirectory(prefix="townlight-owner-manuals-") as temporary:
        folder = Path(temporary)
        output = folder / "rendered"
        output.mkdir()
        profile = folder / "libreoffice-profile"
        run([soffice, "-env:UserInstallation=" + profile.as_uri(), "--headless",
             "--convert-to",
             'pdf:writer_pdf_Export:{"UseTaggedPDF":{"type":"boolean","value":"true"}}',
             "--outdir", str(output), *map(str, docx_paths)])
        for docx in docx_paths:
            rendered_pdf = output / (docx.stem + ".pdf")
            if not rendered_pdf.is_file() or not rendered_pdf.stat().st_size:
                raise RuntimeError(f"LibreOffice did not produce {rendered_pdf}")
            pdf = ROOT / "pdf" / rendered_pdf.name
            shutil.copyfile(rendered_pdf, pdf)
            print(f"Rendered {pdf.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
