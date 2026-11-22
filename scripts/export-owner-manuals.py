"""Insert maintained candidate notes into existing owner manual editions.

This keeps the accepted site layout, section anchors, Word artwork and links.
Only the scoped candidate notes and the PDFs rendered from the updated Word
files are changed.
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = {
    "suite": ("Townlight Suite Manual", "Townlight-Suite-Manual-Beta-1",
              "The signed Windows 1.9.2.1 candidate adds a city-hosted shared mode", 2),
    "meetings": ("Townlight Meetings Manual", "Townlight-Meetings-Manual-Beta-1",
                 "The signed Suite 1.9.2.1 candidate lets named clerk staff", 1),
    "records": ("Townlight Records Manual", "Townlight-Records-Manual-Beta-1",
                "The signed Suite 1.9.2.1 candidate lets named Records Staff", 2),
    "station": ("Townlight Station Manual", "Townlight-Station-Manual-Beta-1",
                "In the signed Suite 1.9.2.1 candidate, Station capture", 1),
}
PORTAL = ("Townlight Portal guide", "Townlight-Portal-Guide-Beta-1")
HYPERLINK_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"


def run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(
            f"Documentation command failed ({result.returncode}): {arguments[0]}\n"
            f"{result.stdout}{result.stderr}"
        )
    return result


def markdown_to_html(pandoc: str, text: str) -> str:
    result = subprocess.run(
        [pandoc, "-f", "markdown+raw_html", "-t", "html5"], input=text,
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode:
        raise RuntimeError(f"Pandoc failed to render a candidate note:\n{result.stderr}")
    return result.stdout.strip()


def markdown_blocks(source: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", source.strip()) if block.strip()]


def product_note(source: str, start: str, expected: int) -> list[str]:
    blocks = markdown_blocks(source)
    index = next((i for i, block in enumerate(blocks) if block.startswith(start)), None)
    if index is None:
        raise RuntimeError(f"Could not find candidate paragraph starting: {start}")
    selected: list[str] = []
    for block in blocks[index:]:
        if selected and (block.startswith("#") or block.startswith("|")
                         or block.startswith(("- ", "* ", "1. "))):
            break
        selected.append(block)
        if len(selected) == expected:
            break
    if len(selected) != expected:
        raise RuntimeError(f"Expected {expected} candidate paragraph(s) after: {start}")
    return selected


def portal_note(source: str) -> list[str]:
    match = re.search(
        r"(?ms)^## Windows shared-host candidate publication\s*$(.*?)(?=^## |\Z)", source
    )
    if not match:
        raise RuntimeError("Could not find the Portal shared-host candidate section")
    paragraphs = markdown_blocks(match.group(1))
    if len(paragraphs) != 3:
        raise RuntimeError(f"Expected 3 Portal candidate paragraphs, found {len(paragraphs)}")
    return paragraphs


def add_html_note(path: Path, slug: str, paragraphs: list[str], pandoc: str) -> None:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    marker = f"candidate-note-{slug}"
    html_body = markdown_to_html(pandoc, "\n\n".join(paragraphs))
    note = (
        f"<!-- {marker}:begin -->{newline}"
        f'<aside id="{marker}" class="release-note" aria-label="Windows 1.9.2.1 candidate status">'
        f'<p><strong>Windows 1.9.2.1 signed candidate · not distributed.</strong></p>'
        f"{html_body}</aside>{newline}<!-- {marker}:end -->"
    )
    region = re.compile(rf"<!-- {re.escape(marker)}:begin -->.*?<!-- {re.escape(marker)}:end -->", re.S)
    if region.search(text):
        text = region.sub(note, text, count=1)
    else:
        opener = '<main id="main" class="reading wrap">'
        if opener not in text:
            raise RuntimeError(f"Manual wrapper not found in {path}")
        text = text.replace(opener, opener + newline + note, 1)
    path.write_bytes(text.encode("utf-8"))


def add_portal_html_note(path: Path, paragraphs: list[str], pandoc: str) -> None:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    marker = "candidate-note-portal"
    heading = "## Windows shared-host candidate publication"
    body = markdown_to_html(pandoc, heading + "\n\n" + "\n\n".join(paragraphs))
    note = f"<!-- {marker}:begin -->{newline}{body}{newline}<!-- {marker}:end -->"
    region = re.compile(rf"<!-- {re.escape(marker)}:begin -->.*?<!-- {re.escape(marker)}:end -->", re.S)
    if region.search(text):
        text = region.sub(note, text, count=1)
    else:
        anchor = '<h2 id="for-staff-prepare-and-publish">'
        if anchor not in text:
            raise RuntimeError("Portal staff workflow anchor not found")
        text = text.replace(anchor, note + newline + anchor, 1)
    toc_anchor = '<li><a href="#for-staff-prepare-and-publish"'
    toc_item = (
        '<li data-candidate-note="portal"><a href="#windows-shared-host-candidate-publication" '
        'id="toc-windows-shared-host-candidate-publication">Windows shared-host candidate publication</a></li>'
    )
    text = re.sub(r'<li data-candidate-note="portal">.*?</li>', "", text, count=1, flags=re.S)
    if toc_anchor not in text:
        raise RuntimeError("Portal contents list link not found")
    text = text.replace(toc_anchor, toc_item + newline + toc_anchor, 1)
    path.write_bytes(text.encode("utf-8"))


def parse_paragraph(fragment: str) -> tuple[str, str | None]:
    text = "".join(html.unescape(value) for value in
                   re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", fragment, re.S))
    style = re.search(r'<w:pStyle\b[^>]*\bw:val="([^"]+)"', fragment)
    return text, style.group(1) if style else None


def remove_prior_docx_note(document: str, slug: str) -> str:
    name = f"TownlightCandidateNote{slug.title()}"
    start_re = re.compile(rf'<w:bookmarkStart\b(?=[^>]*\bw:name="{re.escape(name)}")(?=[^>]*\bw:id="(\d+)")[^>]*/>')
    start = start_re.search(document)
    if not start:
        return document
    bookmark_id = start.group(1)
    end_re = re.compile(rf'<w:bookmarkEnd\b(?=[^>]*\bw:id="{bookmark_id}")[^>]*/>')
    end = end_re.search(document, start.end())
    if not end:
        raise RuntimeError(f"Candidate note bookmark end is missing for {slug}")
    paragraphs = list(re.finditer(r"<w:p(?:\s[^>]*)?>.*?</w:p>", document, re.S))
    begin_p = next((m for m in paragraphs if start.start() >= m.start() and start.end() <= m.end()), None)
    end_p = next((m for m in paragraphs if end.start() >= m.start() and end.end() <= m.end()), None)
    if begin_p is None or end_p is None:
        raise RuntimeError(f"Could not locate candidate note paragraphs for {slug}")
    return document[:begin_p.start()] + document[end_p.end():]


def add_relationship(rels: str, url: str) -> tuple[str, str]:
    for match in re.finditer(r"<Relationship\b[^>]*/>", rels):
        attrs = dict(re.findall(r'([A-Za-z]+)="([^"]*)"', match.group()))
        if html.unescape(attrs.get("Target", "")) == url and attrs.get("TargetMode") == "External":
            return rels, attrs["Id"]
    ids = [int(value) for value in re.findall(r'\bId="rId(\d+)"', rels)]
    relation_id = f"rId{max(ids, default=0) + 1}"
    relation = (
        f'<Relationship Id="{relation_id}" Type="{HYPERLINK_REL}" '
        f'Target="{html.escape(url, quote=True)}" TargetMode="External" />'
    )
    if "</Relationships>" not in rels:
        raise RuntimeError("Invalid Word relationships file")
    return rels.replace("</Relationships>", relation + "</Relationships>", 1), relation_id


def run_xml(text: str, *, bold: bool = False) -> str:
    if not text:
        return ""
    props = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return f'<w:r>{props}<w:t xml:space="preserve">{html.escape(text, quote=False)}</w:t></w:r>'


def markdown_runs(text: str, rels: str) -> tuple[str, str]:
    link_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
    marker_pattern = re.compile(r"(\*\*.*?\*\*|__.*?__|`[^`]+`)")
    run_parts: list[str] = []

    def plain_runs(value: str) -> None:
        position = 0
        for marker in marker_pattern.finditer(value):
            run_parts.append(run_xml(value[position:marker.start()]))
            token = marker.group()
            if token.startswith(("**", "__")):
                run_parts.append(run_xml(token[2:-2], bold=True))
            else:
                run_parts.append(run_xml(token[1:-1]))
            position = marker.end()
        run_parts.append(run_xml(value[position:]))

    position = 0
    for match in link_pattern.finditer(text):
        plain_runs(text[position:match.start()])
        rels, relation_id = add_relationship(rels, match.group(2))
        label = html.escape(match.group(1), quote=False)
        run_parts.append(
            f'<w:hyperlink r:id="{relation_id}"><w:r><w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr>'
            f'<w:t xml:space="preserve">{label}</w:t></w:r></w:hyperlink>'
        )
        position = match.end()
    plain_runs(text[position:])
    return "".join(run_parts), rels


def note_paragraph(text: str, rels: str, *, bold: bool = False) -> tuple[str, str]:
    if bold:
        runs = run_xml(text, bold=True)
    else:
        runs, rels = markdown_runs(text, rels)
    return f'<w:p><w:pPr><w:pStyle w:val="Normal"/></w:pPr>{runs}</w:p>', rels


def patch_docx(path: Path, slug: str, title: str, paragraphs: list[str]) -> dict[str, str]:
    with ZipFile(path, "r") as source_zip:
        files = [(info, source_zip.read(info.filename)) for info in source_zip.infolist()]
    payloads = {info.filename: data for info, data in files}
    document = payloads["word/document.xml"].decode("utf-8")
    rels = payloads["word/_rels/document.xml.rels"].decode("utf-8")
    before_media = {name: data for name, data in payloads.items() if name.startswith("word/media/")}
    document = remove_prior_docx_note(document, slug)

    p_matches = list(re.finditer(r"<w:p(?:\s[^>]*)?>.*?</w:p>", document, re.S))
    title_match = None
    for match in p_matches:
        text, style = parse_paragraph(match.group())
        if text == title and style in ("Heading1", "Title") and "<w:hyperlink" not in match.group():
            title_match = match
            break
    if title_match is None:
        raise RuntimeError(f"Could not find the main title paragraph in {path.name}")

    bookmark_name = f"TownlightCandidateNote{slug.title()}"
    existing_ids = [int(v) for v in re.findall(r'<w:bookmarkStart\b[^>]*\bw:id="(\d+)"', document)]
    bookmark_id = max(existing_ids, default=0) + 1
    paragraphs_xml: list[str] = []
    label = "Windows 1.9.2.1 signed candidate · not publicly distributed"
    label_xml, rels = note_paragraph(label, rels, bold=True)
    paragraphs_xml.append(label_xml)
    for markdown in paragraphs:
        p_xml, rels = note_paragraph(markdown, rels)
        paragraphs_xml.append(p_xml)
    paragraphs_xml[0] = paragraphs_xml[0].replace(
        "</w:pPr>",
        f'</w:pPr><w:bookmarkStart w:id="{bookmark_id}" w:name="{bookmark_name}"/>',
        1,
    )
    paragraphs_xml[-1] = paragraphs_xml[-1].replace(
        "</w:p>", f'<w:bookmarkEnd w:id="{bookmark_id}"/></w:p>', 1
    )
    insertion = "".join(paragraphs_xml)
    document = document[:title_match.end()] + insertion + document[title_match.end():]
    payloads["word/document.xml"] = document.encode("utf-8")
    payloads["word/_rels/document.xml.rels"] = rels.encode("utf-8")

    with tempfile.NamedTemporaryFile(prefix="townlight-manual-", suffix=".docx", dir=path.parent, delete=False) as temporary:
        temp_path = Path(temporary.name)
    try:
        with ZipFile(temp_path, "w", ZIP_DEFLATED) as output_zip:
            for info, _data in files:
                output_zip.writestr(info, payloads[info.filename])
        with ZipFile(temp_path, "r") as output_zip:
            after_media = {name: output_zip.read(name) for name in output_zip.namelist()
                           if name.startswith("word/media/")}
        if before_media != after_media:
            raise RuntimeError(f"Word image contents changed while patching {path.name}")
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)
    return {name: __import__("hashlib").sha256(data).hexdigest().upper()
            for name, data in before_media.items()}


def render_tagged_pdfs(docx_paths: list[Path]) -> None:
    soffice = shutil.which("soffice.com") or shutil.which("soffice")
    if not soffice:
        installed = Path("C:/Program Files/LibreOffice/program/soffice.com")
        if installed.is_file():
            soffice = str(installed)
    if not soffice:
        raise RuntimeError("LibreOffice soffice.com is required for PDF conversion")
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
            source_pdf = output / (docx.stem + ".pdf")
            if not source_pdf.is_file() or not source_pdf.stat().st_size:
                raise RuntimeError(f"LibreOffice did not produce {source_pdf}")
            shutil.copyfile(source_pdf, ROOT / "pdf" / source_pdf.name)
            print(f"Rendered tagged pdf/{source_pdf.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True, help="Owner Suite USER-MANUAL.md")
    parser.add_argument("--meetings", type=Path, required=True, help="Owner Meetings USER-MANUAL.md")
    parser.add_argument("--records", type=Path, required=True, help="Owner Records USER-MANUAL.md")
    parser.add_argument("--station", type=Path, required=True, help="Owner Station beta-1/USER-MANUAL.md")
    parser.add_argument("--portal", type=Path, required=True, help="Owner Portal docs/portal/guide.md")
    args = parser.parse_args()
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("Pandoc is required to render the candidate HTML notes")

    paths: list[Path] = []
    for slug, (title, stem, start, count) in PRODUCTS.items():
        source = getattr(args, slug).resolve()
        if not source.is_file():
            raise RuntimeError(f"Owner source is missing: {source}")
        paragraphs = product_note(source.read_text(encoding="utf-8"), start, count)
        html_path = ROOT / "manuals" / f"{slug}.html"
        docx_path = ROOT / "docx" / f"{stem}.docx"
        add_html_note(html_path, slug, paragraphs, pandoc)
        media_hashes = patch_docx(docx_path, slug, title, paragraphs)
        print(f"Updated manuals/{slug}.html and docx/{stem}.docx; preserved {len(media_hashes)} media file(s)")
        paths.append(docx_path)

    portal_source = args.portal.resolve()
    if not portal_source.is_file():
        raise RuntimeError(f"Portal guide source is missing: {portal_source}")
    paragraphs = portal_note(portal_source.read_text(encoding="utf-8"))
    add_portal_html_note(ROOT / "manuals/portal.html", paragraphs, pandoc)
    portal_docx = ROOT / "docx" / f"{PORTAL[1]}.docx"
    media_hashes = patch_docx(portal_docx, "portal", PORTAL[0], paragraphs)
    print(f"Updated manuals/portal.html and docx/{PORTAL[1]}.docx; preserved {len(media_hashes)} media file(s)")
    paths.append(portal_docx)
    render_tagged_pdfs(paths)


if __name__ == "__main__":
    main()
