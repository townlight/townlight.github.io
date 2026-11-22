<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/svg/townlight-hall-lockup-tagline-reversed.svg">
    <img alt="Townlight — Municipal software cities can actually own." src="brand/svg/townlight-hall-lockup-tagline.svg" width="600">
  </picture>
</p>

[Download signed Windows beta 1.9.2.1](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/Townlight-Windows-x64-1.9.2.1.msi) · [Release catalog](https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.2.1) · [SHA-256 checksums](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/SHA256SUMS-Windows-1.9.2.1.txt) · [Public announcement](https://townlight.github.io/announcement.html) · [Support and feedback](https://townlight.github.io/support.html)

Windows 1.9.2.1 is the current signed public beta. Its [acceptance summary](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/ACCEPTANCE-Windows-1.9.2.1.md) covers revisioned council packets, shared work between Windows environments, and delivery of explicitly approved material to a separately configured portal. Direct upgrades from earlier releases were not tested.

## Windows 1.9.2.1 release

The accepted MSI was tested on a physical Windows host and a clean Windows Sandbox guest on the same computer using synthetic data and a test portal. This does not establish direct-upgrade, two-physical-PC, replacement-computer or live city-network acceptance. Read the [release guide](https://townlight.github.io/manuals/windows-1.9.2.1-candidate.html), [acceptance summary](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/ACCEPTANCE-Windows-1.9.2.1.md) and [corresponding-source archive](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/Townlight-Windows-1.9.2.1-Corresponding-Source.zip).

# Townlight — Townlight Beta 1

## Shared meeting imports · Windows 1.8.1.1

Windows 1.8.1.1 adds shared meeting imports for 31 source families, with 34 supported source/format pairs. Installed Windows Sandbox checks exercised preview, save and durable readback using public captures and fixtures, plus the documented Townlight handoffs. These checks do not establish automatic discovery on every live portal or a complete retest of every module.

[All 31 sources, formats and handoffs](https://townlight.github.io/manuals/meeting-imports.html) · [Installed acceptance](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.8.1.1/ACCEPTANCE-Windows-1.8.1.1.md).

Windows 1.9.1.1 was the previous signed public beta. Its release and version-specific acceptance remain available with the original artifact identities.

Windows 1.9.1.1 included Townlight Runtime 0.3.3; Windows 1.9.2.1 includes Runtime 0.3.4. The 1.9.2.1 release's exact component sources and archive hashes are listed in `reference/windows-1.9.2.1-source-pins.json`.


Kept municipal products: Core, Records, Meetings, Code, Access, Notice, Zoning,
Planning, Permitting, Inspections, Station, Boards & Commissions, Contracts, and Procurement.

[Townlight website](https://townlight.github.io/) · [Suite manual](https://townlight.github.io/manuals/suite.html) ·
[Signed Windows x64 beta 1.9.1.1](https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.9.1.1) ·
[Versions, provenance and limits](https://townlight.github.io/versions.html)

Windows 1.8.1.1 adds shared meeting imports for 31 source families, with 34 supported source/format pairs. Installed Windows Sandbox checks exercised preview, save and durable readback using public captures and fixtures, plus the documented Townlight handoffs. These checks do not establish automatic discovery on every live portal or a complete retest of every module.

| Product | Manual | Source |
|---|---|---|
| Core | [Manual](https://townlight.github.io/manuals/core.html) | [Repository](https://github.com/townlight/core) |
| Records | [Manual](https://townlight.github.io/manuals/records.html) | [Repository](https://github.com/townlight/sunshine) |
| Meetings | [Manual](https://townlight.github.io/manuals/meetings.html) | [Repository](https://github.com/townlight/meetings) |
| Code | [Manual](https://townlight.github.io/manuals/code.html) | [Repository](https://github.com/townlight/ordinances) |
| Access | [Manual](https://townlight.github.io/manuals/access.html) | [Repository](https://github.com/townlight/access) |
| Notice | [Manual](https://townlight.github.io/manuals/notice.html) | [Repository](https://github.com/townlight/notice) |
| Zoning | [Manual](https://townlight.github.io/manuals/zoning.html) | [Repository](https://github.com/townlight/zone) |
| Planning | [Manual](https://townlight.github.io/manuals/planning.html) | [Repository](https://github.com/townlight/plan) |
| Permitting | [Manual](https://townlight.github.io/manuals/permitting.html) | [Repository](https://github.com/townlight/permit) |
| Inspections | [Manual](https://townlight.github.io/manuals/inspections.html) | [Repository](https://github.com/townlight/inspect) |
| [Boards & Commissions](https://townlight.github.io/products/boards/) | [Guide](https://townlight.github.io/manuals/windows-staff-workflows.html#boards) | [Repository](https://github.com/townlight/boards) |
| [Contracts](https://townlight.github.io/products/contracts/) | [Guide](https://townlight.github.io/manuals/windows-staff-workflows.html#contracts) | [Repository](https://github.com/townlight/contracts) |
| [Procurement](https://townlight.github.io/products/procurement/) | [Guide](https://townlight.github.io/manuals/windows-staff-workflows.html#procurement) | [Repository](https://github.com/townlight/procure) |
| Station | [Manual](https://townlight.github.io/manuals/station.html) | [Repository](https://github.com/townlight/station) |


Windows 1.8.1.1 acceptance includes the configured Station worker processing a public Wistia MP4 and attaching its output to Records. Historical Station delivery evidence does not establish live broadcast, external upload or city deployment acceptance for this MSI.


## Separately deployed resident portal beta

[Portal release and downloads](https://github.com/townlight/townlight/releases/tag/townlight-beta-1-resident-portal) · [Portal guide](https://townlight.github.io/manuals/portal.html). Includes the approved city-facing website and the Meetings → Station → Records publication workflow. Deploy the portal and matching native bridge separately; the portal and bridge use their own release and deployment steps. Acceptance uses synthetic data; CivicCast remains separate.


[Open Hall brand package and usage guide](https://townlight.github.io/brand/).

## Site source and maintenance

Dependency-free static HTML/CSS/SVG documentation. GitHub Pages serves `main` at
the repository root; `.nojekyll` preserves the portable file layout. `products/`
contains the product landing pages, `manuals/` the operating guides, `api/` exact protocol/schema
references, `pdf/` and `docx/` printable/editable editions, and `reference/`
version/provenance/workflow evidence. `terms.html` includes terms and the full
license; current owned content is AGPL-3.0-only.

Preview with a loopback-only static server. Check relative links, headings, the
first keyboard skip link, visible focus, reduced-motion behavior, image loading,
console errors and desktop/mobile overflow. Preserve the accepted companion ZIP
and its hash; publication banners describe the distribution change separately.
Publishing this site does not install an application or provision a city portal.

The Windows 1.9.2.1 release guide is maintained in
`manuals/windows-1.9.2.1-candidate.md`. Its HTML, PDF and Word editions are
prepared from that source with `python -B scripts/build-candidate-guide.py`.
The file names keep the existing candidate-guide URLs so earlier links continue
to resolve; the editions describe the published 1.9.2.1 release.

The maintained Suite, Meetings, Records and Station manuals are sourced from
their owning repositories' `USER-MANUAL.md` files; the portal guide is sourced
from the Suite repository's `docs/portal/guide.md`. Insert their release
notes with `scripts/export-owner-manuals.py`, passing `--suite`, `--meetings`,
`--records`, `--station` and `--portal` with the respective file paths. The
exporter preserves the existing site HTML, section anchors and Word artwork,
then regenerates tagged PDFs from the updated Word editions. Versioned Windows
Staff Workflows release files keep their original identities and contents.


[Open Hall brand package and usage guide](https://townlight.github.io/brand/).

## Maintain the landing pages

Edit the product copy in `landing/content.py` and the shared layout in
`landing/build.py`. The renderer uses the published source pins in
`reference/windows-1.9.2.1-source-pins.json`. The page style extends the
Open Hall palette and the site's existing tokens in `assets/site.css`.

From the site root:

```powershell
python -B landing/build.py
python -B landing/build.py --check
python -m http.server 8767 --bind 127.0.0.1
```

Open `http://127.0.0.1:8767/` to preview the generated site. You can render
one page with `python -B landing/build.py records`. Commit source and generated
HTML together. Merge to `main` to publish through the existing GitHub Pages
deployment from the repository root.

## Previous release · Windows 1.9.1.1 Station recorder

Windows 1.9.1.1 improves the clerk workflows for Records, Meetings, and Code, adds Open Hall icons, and fixes the ten-second Station preview.

Windows 1.9.1.1 remains available as a historical release. Its acceptance and artifact identities remain scoped to that version.

[Acceptance and limits](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.1.1/ACCEPTANCE-Windows-1.9.1.1.md).
