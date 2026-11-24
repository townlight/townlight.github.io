"""Refresh current owner HTML and Word manuals and export tagged PDFs."""
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
HYPERLINK_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"


def run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(
            f"Documentation command failed ({result.returncode}): {arguments[0]}\n"
            f"{result.stdout}{result.stderr}"
        )
    return result


def markdown_blocks(source: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", source.strip()) if block.strip()]


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


def patch_docx(path: Path, slug: str, title: str, paragraphs: list[str],
               canonical: str, version: str) -> dict[str, str]:
    with ZipFile(path, "r") as source_zip:
        files = [(info, source_zip.read(info.filename)) for info in source_zip.infolist()]
    payloads = {info.filename: data for info, data in files}
    document = payloads["word/document.xml"].decode("utf-8")
    rels = payloads["word/_rels/document.xml.rels"].decode("utf-8")
    before_media = {name: data for name, data in payloads.items() if name.startswith("word/media/")}
    document = remove_prior_docx_note(document, slug)
    document, rels = patch_word_install(document, rels, canonical, version)
    document, rels = patch_word_sections(document, rels, canonical)

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
    label = f"Windows {version} current release"
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


def patch_word_install(document, rels, canonical, version):
    # --- Parse canonical markdown (scoped) ---
    fresh_prose = None
    download_item = None

    m = re.search(r'(?m)^###\s+Fresh installation\s*$', canonical)
    if m:
        rest = canonical[m.end():]
        nm = re.search(r'(?m)^#{1,6}\s', rest)
        section = rest[:nm.start()] if nm else rest
        # Intro paragraph: first non-heading, non-list block
        for para in re.split(r'\n\s*\n', section.strip()):
            stripped = para.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if re.match(r'^(?:[-*+]|\d+[\.\)])\s', stripped):
                continue
            fresh_prose = ' '.join(stripped.split())
            break
        # Download list item within the same section, only
        for line in section.splitlines():
            lm = re.match(r'^\s*(?:[-*+]|\d+[\.\)])\s+(Download\b.*)$', line)
            if lm:
                download_item = lm.group(1).strip()
                break

    target_keys = ('Windows MSI version', 'Released artifact identity', 'Supported acceptance profile')
    md_rows = {}
    for line in canonical.splitlines():
        s = line.strip()
        if not s.startswith('|'):
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if len(cells) < 2 or all(re.fullmatch(r'[-:\s]+', c) for c in cells):
            continue
        key = re.sub(r'[*_`]', '', cells[0]).strip()
        if key in target_keys:
            md_rows[key] = cells

    station_sentence = None
    for line in canonical.splitlines():
        s = line.strip()
        if s.startswith('This manual covers Station') and 'installed with Windows MSI' in s:
            station_sentence = s
            break

    station_replacements = {}
    for prefix in ("The native desktop frontend above is distinct from Station’s browser operator.",
                   "The package/API version is"):
        latest = next((line.strip() for line in canonical.splitlines()
                       if line.strip().startswith(prefix)), None)
        if latest:
            station_replacements[prefix] = latest

    workspace_recovery = next((line.strip().strip('|').split('|')[-1].strip()
                               for line in canonical.splitlines()
                               if line.startswith('| Workspace absent |')), None)
    access_evidence = next((line.strip() for line in canonical.splitlines()
                            if line.lstrip().startswith('`v0.5.0` is an early release. Probe gaps')), None)

    old_run_prefix = ("Run the signed Windows 1.9.1.1 MSI and use an empty database "
                      "and a new Townlight profile for first run.")
    download_prefix = "Download the signed MSI, matching source"

    def rebuild(para, new_runs):
        mopen = re.match(r'<w:p\b[^>]*>', para)
        open_tag = mopen.group(0) if mopen else '<w:p>'
        mppr = re.search(r'<w:pPr\b.*?</w:pPr>', para, re.DOTALL)
        pPr = mppr.group(0) if mppr else ''
        starts = ''.join(re.findall(r'<w:bookmarkStart\b[^>]*/>', para))
        ends = ''.join(re.findall(r'<w:bookmarkEnd\b[^>]*/>', para))
        return open_tag + pPr + starts + new_runs + ends + '</w:p>'

    def sub_para(match):
        nonlocal rels
        para = match.group(0)
        if '<w:drawing' in para:
            return para
        text, _ = parse_paragraph(para)
        text = html.unescape(text)
        new_text = next((latest for prefix, latest in station_replacements.items()
                         if text.startswith(prefix)), None)
        if (station_replacements and text in {"Windows 1.9.1.1 meeting recorder",
                                                  "Historical Windows 1.9.1.1 meeting recorder"}
                and f'## Windows {version} meeting recorder' in canonical):
            new_text = f'Windows {version} meeting recorder'
        elif station_replacements and (text.startswith("Windows 1.9.1.1 is a signed public beta.")
                                       or text == "Windows 1.9.1.1 Station recorder release"):
            return re.sub(r"(<w:t(?:\s[^>]*)?>)", r"\1Historical ", para, count=1)

        if workspace_recovery and text == "Check selected composition; activate through Finish Records Migration; wait for readiness.":
            new_text = workspace_recovery
        elif access_evidence and text.startswith('v0.5.0 is an early release. Probe gaps'):
            new_text = access_evidence
        elif text.startswith(old_run_prefix) and fresh_prose:
            new_text = fresh_prose
        elif text.startswith(download_prefix) and download_item:
            new_text = download_item
        elif station_sentence and text.startswith('This manual covers Station') \
                and 'installed with Windows MSI' in text:
            new_text = station_sentence
        elif text.startswith('Version') and 'included in Windows MSI' in text:
            new_text = re.sub(r'(included in Windows MSI(?:\s+version)?\s+)\d+(?:\.\d+)+',
                              lambda mm: mm.group(1) + version, text)
        else:
            vm = re.match(r'^(Windows x64 Beta 1\s*·\s*MSI\s*)\d+(?:\.\d+)+(.*)$',
                          text, re.I | re.S)
            if vm:
                new_text = vm.group(1) + version + vm.group(2)
            else:
                rm = re.match(r'^(Run the signed Windows\s+)\d+(?:\.\d+)+(?=\s*MSI\b)(.*)$',
                              text, re.I | re.S)
                if rm:
                    new_text = rm.group(1) + version + rm.group(2)

        if new_text is None or new_text == text:
            return para
        new_runs, rels = markdown_runs(new_text, rels)
        return rebuild(para, new_runs)

    document = re.sub(r'<w:p\b[^>]*>.*?</w:p>', sub_para, document, flags=re.DOTALL)

    # --- Table patch: exact map by normalized first-cell label, update only second cell ---
    if md_rows:
        def sub_tbl(match):
            nonlocal rels
            tbl = match.group(0)

            def sub_row(rm):
                nonlocal rels
                row = rm.group(0)
                cells = re.findall(r'<w:tc\b.*?</w:tc>', row, re.DOTALL)
                if len(cells) < 2:
                    return row
                first_para_m = re.search(r'<w:p\b[^>]*>.*?</w:p>', cells[0], re.DOTALL)
                if not first_para_m:
                    return row
                first_text, _ = parse_paragraph(first_para_m.group(0))
                key = re.sub(r'[*_`]', '', html.unescape(first_text)).strip()
                if key not in md_rows:
                    return row
                md_cells = md_rows[key]
                if len(md_cells) < 2:
                    return row
                new_runs, rels = markdown_runs(md_cells[1], rels)

                def repl_p(pm):
                    p = pm.group(0)
                    if '<w:drawing' in p:
                        return p
                    return rebuild(p, new_runs)

                new_cell = re.sub(r'<w:p\b[^>]*>.*?</w:p>', repl_p, cells[1],
                                  count=1, flags=re.DOTALL)
                return row.replace(cells[1], new_cell, 1)

            return re.sub(r'<w:tr\b[^>]*>.*?</w:tr>', sub_row, tbl, flags=re.DOTALL)

        document = re.sub(r'<w:tbl\b[^>]*>.*?</w:tbl>', sub_tbl, document, flags=re.DOTALL)

    return document, rels


def patch_word_sections(document: str, rels: str, canonical: str) -> tuple[str, str]:
    sections, cur = {}, None
    for ln in canonical.split('\n'):
        m = re.match(r'^(#{1,6})\s+(.+?)\s*$', ln)
        if m:
            cur = m.group(2).strip()
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(ln)

    p_re = re.compile(r'<w:p\b[^>]*>.*?</w:p>|<w:p\b[^>]*/>', re.DOTALL)
    paras = []
    for m in p_re.finditer(document):
        txt, sty = parse_paragraph(m.group(0))
        paras.append((m.start(), m.end(), m.group(0), (txt or '').strip(), sty))
    heads = [i for i, p in enumerate(paras) if p[4] and re.match(r'^Heading[1-6]$', p[4])]
    find_head = lambda name: next((i for i in heads if paras[i][3] == name), None)

    def rebuild(xml, runs):
        ppr = re.search(r'<w:pPr\b.*?</w:pPr>', xml, re.DOTALL)
        bs = re.search(r'<w:bookmarkStart\b[^>]*/>', xml)
        be = re.search(r'<w:bookmarkEnd\b[^>]*/>', xml)
        op = re.match(r'<w:p\b[^>]*>', xml)
        return f"{op.group(0) if op else '<w:p>'}{ppr.group(0) if ppr else ''}{bs.group(0) if bs else ''}{runs}{be.group(0) if be else ''}</w:p>"

    def first_prose(idx):
        for i in range(idx + 1, len(paras)):
            if i in heads:
                return None
            if not paras[i][3] or '<w:drawing' in paras[i][2] or '<w:pict' in paras[i][2] or '<w:numPr' in paras[i][2]:
                continue
            return i
        return None

    def canon_prose(name):
        for ln in sections.get(name, []):
            s = ln.strip()
            if s and not s.startswith(('#', '|')) and not re.match(r'^[-*]\s|^\d+\.\s+', s):
                return s
        return None

    edits = []

    def sync_prose(name):
        nonlocal rels
        idx = find_head(name)
        prose = canon_prose(name) if idx is not None else None
        tgt = first_prose(idx) if prose else None
        if tgt is None:
            return
        runs, rels = markdown_runs(prose, rels)
        edits.append((paras[tgt][0], paras[tgt][1], rebuild(paras[tgt][2], runs)))

    for name in ('Using this manual', 'First run', 'Existing installation', 'Source and document control',
                 'Prepare the normally activated synthetic profile', '2. Activate the runtime', 'Complete technical contract'):
        sync_prose(name)
    for name in tuple(sections):
        if name.startswith('Windows staff workflow'):
            word_heading = next((paras[i][3] for i in heads
                                 if paras[i][3].startswith('Windows staff workflow')), None)
            if word_heading and word_heading != name:
                sections[word_heading] = sections[name]
                sync_prose(word_heading)
                break
            if word_heading:
                sync_prose(name)
                break

    idx = find_head('Fresh installation')
    if idx is not None:
        intro, items = None, []
        for ln in sections.get('Fresh installation', []):
            s = ln.strip()
            if not s:
                continue
            m = re.match(r'^\d+\.\s+(.+)$', s)
            if m:
                items.append(m.group(1).strip())
            elif intro is None and not s.startswith(('#', '|')):
                intro = s
        if intro:
            tgt = first_prose(idx)
            if tgt is not None:
                runs, rels = markdown_runs(intro, rels)
                edits.append((paras[tgt][0], paras[tgt][1], rebuild(paras[tgt][2], runs)))
        lps = []
        for i in range(idx + 1, len(paras)):
            if i in heads:
                break
            if '<w:numPr' in paras[i][2] and '<w:drawing' not in paras[i][2]:
                lps.append(i)
        for k, item in enumerate(items[:len(lps)]):
            i = lps[k]
            runs, rels = markdown_runs(item, rels)
            edits.append((paras[i][0], paras[i][1], rebuild(paras[i][2], runs)))
        if len(items) > len(lps) and lps:
            tmpl = paras[lps[-1]][2]
            ppr = re.search(r'<w:pPr\b.*?</w:pPr>', tmpl, re.DOTALL)
            op = re.match(r'<w:p\b[^>]*>', tmpl)
            combined = ''
            for item in items[len(lps):]:
                r, rels = markdown_runs(item, rels)
                combined += f"{op.group(0) if op else '<w:p>'}{ppr.group(0) if ppr else ''}{r}</w:p>"
            pos = paras[lps[-1]][1]
            edits.append((pos, pos, combined))

    for name in ('Beta identity', 'Component versions'):
        idx = find_head(name)
        if idx is None:
            continue
        s_start = paras[idx][1]
        s_end = next((paras[j][0] for j in heads if j > idx and paras[j][4] == 'Heading2'), len(document))
        scope_xml = document[s_start:s_end]
        ctbl = []
        for ln in sections.get(name, []):
            s = ln.strip()
            if s.startswith('|'):
                cells = [c.strip() for c in s.strip('|').split('|')]
                if not all(re.match(r'^[\-:\s]*$', c) for c in cells if c):
                    ctbl.append(cells)
        tm = re.search(r'<w:tbl\b[^>]*>.*?</w:tbl>', scope_xml, re.DOTALL)
        if ctbl and len(ctbl) >= 2 and tm:
            header = ctbl[0]
            data = [r for r in ctbl[1:] if r and r[0] and not all(re.match(r'^[\-:\s]*$', c) for c in r if c)]
            tbl = tm.group(0)
            tbl_off = s_start + tm.start()
            row_re = re.compile(r'<w:tr\b[^>]*>.*?</w:tr>', re.DOTALL)
            cell_re = re.compile(r'<w:tc\b[^>]*>.*?</w:tc>', re.DOTALL)
            rows = []
            for rm in row_re.finditer(tbl):
                cells = [cm.group(0) for cm in cell_re.finditer(rm.group(0))]
                texts = [parse_paragraph(cx)[0] for cx in cells]
                rows.append({'xml': rm.group(0), 'cells': cells, 'texts': texts,
                             'start': tbl_off + rm.start(), 'end': tbl_off + rm.end()})

            def patch_cell(cx, text, r):
                runs, r2 = markdown_runs(text, r)
                tcpr = re.search(r'<w:tcPr\b.*?</w:tcPr>', cx, re.DOTALL)
                op = re.match(r'<w:tc\b[^>]*>', cx)
                paragraph = p_re.search(cx)
                if paragraph:
                    return cx[:paragraph.start()] + rebuild(paragraph.group(0), runs) + cx[paragraph.end():], r2
                return f"{op.group(0) if op else '<w:tc>'}{tcpr.group(0) if tcpr else ''}<w:p>{runs}</w:p></w:tc>", r2

            if rows and rows[0]['texts'] and header and rows[0]['texts'][0].strip() == header[0]:
                row_map = {r['texts'][0].strip(): r for r in rows[1:] if r['texts']}
                for rdata in data:
                    label = rdata[0]
                    if label in row_map:
                        er = row_map[label]
                        ncs = list(er['cells'])
                        for ci in range(1, min(len(rdata), len(ncs))):
                            ncs[ci], rels = patch_cell(ncs[ci], rdata[ci], rels)
                        op = re.match(r'<w:tr\b[^>]*>', er['xml'])
                        trpr = re.search(r'<w:trPr\b.*?</w:trPr>', er['xml'], re.DOTALL)
                        edits.append((er['start'], er['end'],
                                      f"{op.group(0) if op else '<w:tr>'}{trpr.group(0) if trpr else ''}{''.join(ncs)}</w:tr>"))
                if len(header) >= 3 and len(rows) >= 2:
                    extra = [r for r in data if r[0] not in row_map]
                    if extra:
                        last = rows[-1]
                        base = re.sub(r'<w:bookmarkStart\b[^>]*/>|<w:bookmarkEnd\b[^>]*/>', '', last['xml'])
                        base_cells = [cm.group(0) for cm in cell_re.finditer(base)]
                        combined = ''
                        for rdata in extra:
                            ncs = []
                            for ci in range(len(rdata)):
                                if ci < len(base_cells):
                                    c, rels = patch_cell(base_cells[ci], rdata[ci], rels)
                                    ncs.append(c)
                                else:
                                    r, rels = markdown_runs(rdata[ci], rels)
                                    ncs.append(f"<w:tc><w:p>{r}</w:p></w:tc>")
                            op = re.match(r'<w:tr\b[^>]*>', last['xml'])
                            trpr = re.search(r'<w:trPr\b.*?</w:trPr>', last['xml'], re.DOTALL)
                            combined += f"{op.group(0) if op else '<w:tr>'}{trpr.group(0) if trpr else ''}{''.join(ncs)}</w:tr>"
                        edits.append((last['end'], last['end'], combined))

    existing = canon_prose('Existing installation')
    fresh = find_head('Fresh installation')
    if existing and fresh is not None and find_head('Existing installation') is None:
        next_heading = next((paras[i][0] for i in heads if i > fresh), None)
        if next_heading is not None:
            heading, rels = note_paragraph('Existing installation', rels, bold=True)
            heading = heading.replace('w:val="Normal"', 'w:val="Heading3"', 1)
            prose, rels = note_paragraph(existing, rels)
            edits.append((next_heading, next_heading, heading + prose))

    edits.sort(key=lambda e: e[0], reverse=True)
    out = document
    for s, e, n in edits:
        out = out[:s] + n + out[e:]
    return out, rels


def sync_html(source, target, shell, title, owner_repo):
    import subprocess, re, html
    from pathlib import Path

    source_p = Path(source)
    target_p = Path(target)
    shell_p = Path(shell)

    md = source_p.read_text(encoding='utf-8')

    body = subprocess.check_output(
        ["pandoc", "--from=markdown+raw_html", "--to=html5"],
        input=md, text=True, encoding="utf-8",
    )

    shell_html = shell_p.read_text(encoding='utf-8')
    mm = re.search(r'(<main\b[^>]*>)(.*?)(</main>)', shell_html, re.S | re.I)
    if not mm:
        raise RuntimeError('Shell has no <main>')

    old_inner = ''
    if target_p.exists():
        old_html = target_p.read_text(encoding='utf-8')
        mo = re.search(r'<main\b[^>]*>(.*?)</main>', old_html, re.S | re.I)
        if mo:
            old_inner = mo.group(1)

    def map_url(mo):
        attr, q, url = mo.group(1), mo.group(2), mo.group(3)
        if not url or url.startswith('#') or re.match(
            r'^[a-zA-Z][a-zA-Z0-9+.-]*:', url
        ) or url.startswith('//'):
            return mo.group(0)
        if attr.lower() == 'href':
            if url.startswith('docs/beta-1/'):
                new = '../' + url[len('docs/beta-1/'):]
            elif url.startswith('docs/') or url in ('README.md', 'CHANGELOG.md'):
                new = f'https://github.com/{owner_repo}/blob/HEAD/{url}'
            else:
                return mo.group(0)
        elif attr.lower() == 'src':
            if url.startswith(('http://', 'https://', '//', 'data:')):
                return mo.group(0)
            new = f'https://raw.githubusercontent.com/{owner_repo}/HEAD/{url}'
        else:
            return mo.group(0)
        return f'{attr}={q}{new}{q}'

    body = re.sub(r'\b(href|src)\s*=\s*(["\'])(.*?)\2', map_url, body,
                  flags=re.I | re.S)

    heading_ids = re.compile(r'<h[1-6]\b[^>]*\bid=["\']([^"\']+)["\'][^>]*>', re.I)
    new_headings = {match.group(1): match.start() for match in heading_ids.finditer(body)}
    new_ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', body, re.I))

    def heading_key(identifier):
        return tuple(word for word in identifier.split("-") if word not in {"historical", "previous"})

    insertions = []
    for old_heading in heading_ids.finditer(old_inner):
        identifier = old_heading.group(1)
        if identifier in new_ids:
            continue
        matches = [position for new_id, position in new_headings.items()
                   if heading_key(new_id) == heading_key(identifier)]
        if len(matches) == 1:
            insertions.append((matches[0], f'<span id="{html.escape(identifier, quote=True)}"></span>'))
            new_ids.add(identifier)

    for position, alias in sorted(insertions, reverse=True):
        body = body[:position] + alias + body[position:]

    out = shell_html[:mm.start(2)] + body + shell_html[mm.end(2):]
    out, title_count = re.subn(r"<title>.*?</title>", lambda _: f"<title>{html.escape(title)}</title>",
                              out, count=1, flags=re.S | re.I)
    if not title_count:
        raise RuntimeError("Shell has no <title>")
    target_p.parent.mkdir(parents=True, exist_ok=True)
    target_p.write_text(out, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Export Townlight site.")
    parser.add_argument("--suite", required=True, help="Suite canonical Markdown")
    parser.add_argument("--owner-root", required=True, help="Parent directory of owner repo snapshots")
    parser.add_argument("--only", nargs="*", help="Optional subset of slugs")
    parser.add_argument("--html-only", action="store_true")
    args = parser.parse_args()

    mapping = {
        "suite":       ("Suite",       "townlight"),
        "core":        ("Core",        "core"),
        "records":     ("Records",     "sunshine"),
        "meetings":    ("Meetings",    "meetings"),
        "code":        ("Code",        "ordinances"),
        "access":      ("Access",      "access"),
        "notice":      ("Notice",      "notice"),
        "zoning":      ("Zoning",      "zone"),
        "planning":    ("Planning",    "plan"),
        "permitting":  ("Permitting",  "permit"),
        "inspections": ("Inspections", "inspect"),
        "station":     ("Station",     "station"),
        "boards":      ("Boards",      "boards"),
        "contracts":   ("Contracts",   "contracts"),
        "procurement": ("Procurement", "procure"),
        "data":        ("Data",        "data"),
        "budget":      ("Budget",      "budget"),
        "grants":      ("Grants",      "grants"),
    }

    only = set(args.only) if args.only else None
    owner_root = Path(args.owner_root)
    manuals_dir = ROOT / "manuals"
    shell = manuals_dir / "core.html"
    title_suffix = " | Townlight Windows Beta 1"
    docx_dir = ROOT / "docx"

    release_re = re.compile(r"^## Windows ([0-9.]+) current release[ \t]*$", re.MULTILINE)
    next_heading_re = re.compile(r"^#", re.MULTILINE)

    docx_paths = []
    slugs = list(mapping.keys())

    for index, slug in enumerate(slugs):
        if only is not None and slug not in only:
            continue

        product, repo_dir = mapping[slug]
        owner_repo = f"townlight/{repo_dir}"

        if slug == "suite":
            canonical = Path(args.suite)
        elif slug == "station":
            canonical = owner_root / "station" / "beta-1" / "USER-MANUAL.md"
        else:
            canonical = owner_root / repo_dir / "USER-MANUAL.md"

        html_title = f"Townlight {product} Manual{title_suffix}"
        html_target = manuals_dir / f"{slug}.html"
        sync_html(canonical, html_target, html_target if html_target.exists() else shell,
                  html_title, owner_repo)
        print(html_target)

        if index < 12 and not args.html_only:
            content = canonical.read_text(encoding="utf-8")
            paragraphs = []
            m = release_re.search(content)
            if m is None:
                raise RuntimeError(f"Current Windows release section missing in {canonical}")
            else:
                start = m.end()
                m2 = next_heading_re.search(content, start)
                end = m2.start() if m2 else len(content)
                section = content[start:end].strip()
                if section:
                    paragraphs = markdown_blocks(section)
            if slug == 'suite':
                download = next((block for block in markdown_blocks(content)
                                 if block.startswith('Authorized Records staff signed into the shared Windows workstation')
                                 and 'Download private attachment' in block), None)
                if download and not any('Download private attachment' in para for para in paragraphs):
                    paragraphs.append(download)

            docx_path = docx_dir / f"Townlight-{product}-Manual-Beta-1.docx"
            word_title = (f"Townlight {product} User Manual" if slug in {"access", "notice"}
                          else f"Townlight {product} Manual")
            patch_docx(docx_path, slug, word_title, paragraphs, content, m.group(1))
            docx_paths.append(docx_path)
            print(docx_path)

    if docx_paths and not args.html_only:
        render_tagged_pdfs(docx_paths)
        print(ROOT / "pdf")


if __name__ == "__main__":
    main()
