<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/svg/townlight-hall-lockup-tagline-reversed.svg">
    <img alt="Townlight — Municipal software cities can actually own." src="brand/svg/townlight-hall-lockup-tagline.svg" width="600">
  </picture>
</p>

[Download Windows beta 1.8.1.1](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.8.1.1/Townlight-Windows-x64-1.8.1.1.msi) · [Public announcement](https://townlight.github.io/announcement.html) · [Support and feedback](https://townlight.github.io/support.html)

Windows 1.8.1.1 has fresh-install acceptance. An in-place upgrade to 1.8.1.1 was not exercised. The previous Windows 1.8.0.1 release tested upgrade from 1.7.2.1; that result applies to 1.8.0.1. Before an existing-city evaluation, back up city data and settings, close Townlight, keep the existing %LOCALAPPDATA%\CivicSuite profile, and use the same Windows account. Keep the prior installer and a restore path. Station continues to use its separately configured service.

# Townlight — Townlight Beta 1

## Shared meeting imports · Windows 1.8.1.1

Windows 1.8.1.1 adds shared meeting imports for 31 source families, with 34 supported source/format pairs. Installed Windows Sandbox checks exercised preview, save and durable readback using public captures and fixtures, plus the documented Townlight handoffs. These checks do not establish automatic discovery on every live portal or a complete retest of every module.

[All 31 sources, formats and handoffs](https://townlight.github.io/manuals/meeting-imports.html) · [Installed acceptance](https://github.com/townlight/townlight/releases/download/townlight-windows-v1.8.1.1/ACCEPTANCE-Windows-1.8.1.1.md).

Windows 1.8.1.1 has fresh-install acceptance. An in-place upgrade to 1.8.1.1 was not exercised. The previous Windows 1.8.0.1 release tested upgrade from 1.7.2.1; that result applies to 1.8.0.1. Before an existing-city evaluation, back up city data and settings, close Townlight, keep the existing %LOCALAPPDATA%\CivicSuite profile, and use the same Windows account. Keep the prior installer and a restore path. Station continues to use its separately configured service.

The accepted MSI contains Townlight Runtime 0.3.1 and Meetings 1.0.6 distributions. Its health version strings still report Runtime 0.3.0 and Meetings 1.0.5. Default-branch source corrects those display strings; the signed MSI and its exact build source remain unchanged.


Kept municipal products: Core, Records, Meetings, Code, Access, Notice, Zoning,
Planning, Permitting, Inspections, Station, Boards & Commissions, Contracts, and Procurement.

[Townlight website](https://townlight.github.io/) · [Suite manual](https://townlight.github.io/manuals/suite.html) ·
[Signed Windows x64 beta 1.8.1.1](https://github.com/townlight/townlight/releases/tag/townlight-windows-v1.8.1.1) ·
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


[Open Hall brand package and usage guide](https://townlight.github.io/brand/).

## Maintain the landing pages

Edit the product copy in `landing/content.py` and the shared layout in
`landing/build.py`. The renderer uses the published source pins in
`reference/windows-1.8.0.1-source-pins.json`. The page style extends the
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
