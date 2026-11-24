"""Render the landing pages for the existing branch-based GitHub Pages site."""

import argparse
import json
import re
from html import escape
from pathlib import Path

from content import GROUPS, PARKED, PRODUCTS

SITE = Path(__file__).resolve().parent.parent
VERSION = "1.9.3.2"
TAG = f"townlight-windows-v{VERSION}"
RELEASE = f"https://github.com/townlight/townlight/releases/tag/{TAG}"
ASSETS = f"https://github.com/townlight/townlight/releases/download/{TAG}"
MSI = f"{ASSETS}/Townlight-Windows-x64-{VERSION}.msi"
ACCEPTANCE = f"{ASSETS}/ACCEPTANCE-Windows-{VERSION}.md"
CHECKSUMS = f"{ASSETS}/SHA256SUMS-Windows-{VERSION}.txt"
PINS = json.loads((SITE / f"reference/windows-{VERSION}-source-pins.json").read_text(encoding="utf-8"))
PUBLIC_SITE = "https://townlight.github.io"
RELEASE_GUIDE = ACCEPTANCE


def link(label, url, css_class=None):
    classes = f' class="{escape(css_class)}"' if css_class else ""
    return f'<a href="{escape(url)}"{classes}>{escape(label)}</a>'


def links(items):
    return '<ul class="landing-link-list">' + "".join(
        f"<li>{link(label, url)}</li>" for label, url in items
    ) + "</ul>"


def actions(primary, secondary):
    return '<div class="actions">' + link(*primary, "button primary") + link(*secondary, "button") + "</div>"


def page(title, description, route, guide, repository, main, nav=None):
    nav = nav or [("Products", "/#products"), ("Guide", guide), ("Download", MSI), ("Source", repository)]
    nav_html = "\n        ".join(link(label, url) for label, url in nav)
    release_notice = "" if any(route == f"/products/{slug}/" for slug in PARKED) else (
        f'<aside class="release-note" aria-label="Current release"><p><strong>Current release:</strong> '
        f'Townlight for Windows {VERSION} is a signed public beta. Private Records staff attachment downloads verify expected file size and SHA-256 before saving; '
        f'Station operator controls work through session renewal. Release acceptance defines tested workflows and limits; it does not claim every module was retested. '
        f'{link("Download MSI", MSI)} · {link("Release catalog", RELEASE)} · {link("SHA-256 checksums", CHECKSUMS)} · '
        f'{link("Acceptance and limits", ACCEPTANCE)} · {link("Versions", "/versions.html")}</p></aside>\n'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <link rel="canonical" href="{PUBLIC_SITE}{route}">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:image" content="{PUBLIC_SITE}/brand/png/townlight-hall-social-preview.png">
  <link rel="icon" href="/brand/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/brand/png/townlight-hall-app-icon-180.png">
  <link rel="stylesheet" href="/assets/site.css">
  <link rel="stylesheet" href="/assets/landing.css">
</head>
<body class="landing">
  <a class="skip" href="#main">Skip to content</a>
  <header class="masthead">
    <div class="landing-wrap masthead-inner">
      <a href="/" aria-label="Townlight home">
        <img src="/brand/svg/townlight-hall-lockup.svg" alt="Townlight" width="161" height="34">
      </a>
      <nav aria-label="Main navigation">
        {nav_html}
      </nav>
    </div>
  </header>
  <main id="main">
{main}
  </main>
{release_notice}  <footer class="landing-footer">
    <div class="landing-wrap">
      <span>Townlight · Open source municipal software</span>
      {links([("Support", "/support.html"), ("Versions", "/versions.html"), ("Brand", "/brand/"), ("Terms and license", "/terms.html")])}
    </div>
  </footer>
</body>
</html>
"""


def workflow(title, steps):
    items = "\n".join(
        f"        <li><strong>{escape(label)}</strong><span>{escape(detail)}</span></li>"
        for label, detail in steps
    )
    return f"""<figure class="workflow-sheet">
      <figcaption><span class="eyebrow">Workflow guide</span>{escape(title)}</figcaption>
      <ol>
{items}
      </ol>
      <p class="sheet-note">Illustrated workflow · staff review at each decision</p>
    </figure>"""


def hero(eyebrow, headline, intro, primary, secondary, workflow_title, steps, release_line, extra_action=None):
    hero_actions = actions(primary, secondary)
    if extra_action:
        hero_actions = hero_actions.removesuffix('</div>') + link(*extra_action, 'button') + '</div>'
    return f"""  <section class="landing-hero" aria-labelledby="title">
    <div class="landing-wrap hero-layout">
      <div>
        <div class="eyebrow">{escape(eyebrow)}</div>
        <h1 id="title">{escape(headline)}</h1>
        <p class="hero-copy">{escape(intro)}</p>
        {hero_actions}
        <p class="release-line">{escape(release_line)}</p>
      </div>
      {workflow(workflow_title, steps)}
    </div>
  </section>"""


def capabilities(features, heading, eyebrow):
    blocks = "\n".join(
        f"        <article><h3>{escape(label)}</h3><p>{escape(detail)}</p></article>"
        for label, detail in features
    )
    return f"""  <section class="landing-section" aria-labelledby="capabilities">
    <div class="landing-wrap">
      <div class="eyebrow">{escape(eyebrow)}</div>
      <h2 id="capabilities">{escape(heading)}</h2>
      <div class="capability-columns">
{blocks}
      </div>
    </div>
  </section>"""


COMPONENT_VERSIONS = {
    "core": ("townlight-core", "1.3.0.dev2"),
    "records": ("townlight-records", "1.8.0.dev4"),
    "meetings": ("townlight-meetings", "1.0.6"),
    "code": ("townlight-code", "1.0.9"),
    "zoning": ("townlight-zoning", "0.2.3"),
    "planning": ("townlight-planning", "0.4.0.dev2"),
    "permitting": ("townlight-permitting", "0.3.0+dev.2"),
    "inspections": ("townlight-inspections", "0.3.0+dev.2"),
    "station": ("townlight-station", "0.4.4"),
    "access": ("townlight-access", "0.5.0"),
    "notice": ("townlight-notice", "0.3.0"),
    "boards": ("townlight-boards", "0.2.1"),
    "contracts": ("townlight-contracts", "0.2.1"),
    "procurement": ("townlight-procurement", "0.3.1"),
    "data": ("townlight-data", "0.2.0"),
    "budget": ("townlight-budget", "0.2.0"),
    "grants": ("townlight-grants", "0.3.0"),
}


def release_notice(slug, summary):
    safe_slug = escape(slug)
    heading = f"candidate-{safe_slug}"
    component_identity = '<p class="component-version">Townlight Windows 1.9.3.2 is the current signed public beta.</p>' if slug == "home" else ""
    edition_label = ""
    if slug != "home":
        distribution, component_version = COMPONENT_VERSIONS[slug]
        edition_label = " · Townlight Beta 1" if slug in {"planning", "permitting", "inspections"} else ""
        component_identity = (
            f'<p class="component-version">Townlight {escape(PRODUCTS[slug]["name"])} '
            f'v{escape(component_version)} is packaged with Windows beta {VERSION}; '
            f'distribution <code>{escape(distribution)}</code>.</p>'
        )
    if slug == "data":
        component_identity += '<p class="component-version">No live CKAN publication.</p>'
    if slug == "budget":
        component_identity = (
            '<p class="component-version"><strong>v0.2.0 packaged with Windows beta 1.9.3.2.</strong> '
            f'Townlight Budget v0.2.0 is packaged with Windows beta {VERSION}. Recovery status: '
            '<a href="https://github.com/townlight/budget/blob/main/docs/release-recovery-status.md">'
            'release-recovery-status.md</a>. This package statement does not imply production readiness.</p>'
        )
    current = f"""  <section class="landing-section landing-band" aria-labelledby="{heading}">
    <div class="landing-wrap">
      <div class="eyebrow">Signed public beta · Windows {VERSION}{edition_label}</div>
      <h2 id="{heading}">Windows {VERSION}</h2>
      {component_identity}
      <p class="section-intro">Private Records staff attachment downloads verify expected file size and SHA-256 before saving; Station operator controls work through session renewal. Release acceptance defines the tested workflows and limits; it does not claim every module was retested.</p>
      {links([(f"Windows {VERSION} installer", MSI), ("Release catalog", RELEASE), ("SHA-256 checksums", CHECKSUMS), ("Acceptance and limits", ACCEPTANCE)])}
    </div>
  </section>"""
    if not summary:
        return current
    match = re.search(r"(?<![\d.])(1\.\d+\.\d+\.\d+)(?![\d.])", summary)
    if not match:
        raise ValueError("summary must name a historical Windows version")
    version = match.group(1)
    hist_release = RELEASE.replace(VERSION, version)
    hist_acceptance = ACCEPTANCE.replace(VERSION, version)
    hist_heading = f"previous-{escape(version.replace('.', '-'))}"
    return current + f"""
  <section class="landing-section landing-band" aria-labelledby="{hist_heading}">
    <div class="landing-wrap">
      <div class="eyebrow">Previous release</div>
      <h2 id="{hist_heading}">Previous release: Windows {version}</h2>
      <p class="section-intro">{escape(summary)}</p>
      {links([(f"Windows {version} acceptance", hist_acceptance), ("Release catalog", hist_release), ("Acceptance and limits", hist_acceptance)])}
    </div>
  </section>"""


def product_page(slug):
    p = PRODUCTS[slug]
    guide = p.get("guide", f"/manuals/{slug}.html")
    api = p.get("api", f"/api/{slug}.html")
    repository = f"https://github.com/townlight/{p['repo']}"
    pin = PINS["repositories"][p["repo"]]["commit"]
    status = p.get("status", "Windows public beta")
    product = f"Townlight {p['name']}"
    heading = hero(
        f"{product} / {p['category']}", p["headline"], p["intro"],
        ("Read the operating guide", guide), ("View Windows release", RELEASE),
        p["workflow"], p["steps"], f"{status} · Townlight {VERSION} · AGPL-3.0-only",
    )
    release = release_notice(slug, p.get("release"))
    release_markup = f"\n{release}" if release else ""
    diagram = ""
    if p.get("diagram"):
        diagram = f"""
      <details>
        <summary>View the {escape(p['name'])} architecture diagram</summary>
        <img class="landing-diagram" loading="lazy" src="/assets/{p['diagram']}-architecture.svg"
          alt="{escape(product)} architecture. The operating guide describes the services and workflow in text.">
      </details>"""
    technical_links = [
        ("Released component source", f"{repository}/tree/{pin}"),
        ("API reference", api),
    ]
    if p.get("owner_manual"):
        technical_links.append(("Owner manual (Markdown)", p["owner_manual"]))
    if p.get("staff_guide"):
        technical_links.append(("Windows staff workflow", p["staff_guide"]))
    technical_links.append(("Repository and contributions", repository))
    body = f"""{heading}{release_markup}
{capabilities(p["features"], f"What {p['name']} supports", "Inside the workflow")}
  <section class="landing-section landing-band" aria-labelledby="getting-started">
    <div class="landing-wrap landing-split">
      <div>
        <div class="eyebrow">Evaluate locally</div>
        <h2 id="getting-started">Start with one real workflow.</h2>
        <p>{escape(p['setup'])}</p>
        {links([("Operating guide", guide), ("Release and checksums", RELEASE)])}
      </div>
      <div class="landing-panel">
        <h3>Scope of this beta</h3>
        <p>{escape(p['limits'])}</p>
        {link("Read the installed acceptance", ACCEPTANCE)}
      </div>
    </div>
  </section>
  <section class="landing-section" aria-labelledby="technical">
    <div class="landing-wrap">
      <div class="eyebrow">For technical teams</div>
      <h2 id="technical">Inspect the implementation.</h2>
      <p class="section-intro">Trace the workflow to the component source pinned by the Windows release. Use the reference for integration details and the repository to report an issue or contribute a change.</p>
      {links(technical_links)}
{diagram}
    </div>
  </section>"""
    return page(product, p["intro"], f"/products/{slug}/", guide, repository, body)


def parked_page(slug):
    p = PARKED[slug]
    repository = f"https://github.com/townlight/{p['repo']}"
    suite = "/versions.html"
    product = f"Townlight {p['name']}"
    status = """<figure class="workflow-sheet">
      <figcaption><span class="eyebrow">Status</span>Parked foundation</figcaption>
      <ol>
        <li><strong>Not a completed product</strong><span>The repository holds exploratory and support code.</span></li>
        <li><strong>Outside the Windows suite</strong><span>The Townlight Windows installer does not install or support it.</span></li>
        <li><strong>Open for review</strong><span>The source stays public under its open source license.</span></li>
      </ol>
      <p class="sheet-note">Status taken from the notice in the repository README</p>
    </figure>"""
    body = f"""  <section class="landing-hero" aria-labelledby="title">
    <div class="landing-wrap hero-layout">
      <div>
        <div class="eyebrow">{escape(product)} / {escape(p['category'])}</div>
        <h1 id="title">{escape(p['headline'])}</h1>
        <p class="hero-copy">{escape(p['intro'])}</p>
        {actions(("View the source", repository), ("See the released Windows suite", suite))}
        <p class="release-line">Parked foundation · Not in the Windows release · AGPL-3.0</p>
      </div>
      {status}
    </div>
  </section>
{capabilities(p["features"], f"What the {p['name']} foundation contains", "Inside the repository")}
  <section class="landing-section landing-band" aria-labelledby="status">
    <div class="landing-wrap landing-split">
      <div>
        <div class="eyebrow">Current status</div>
        <h2 id="status">Parked, and outside the released suite.</h2>
        <p>{escape(product)} is a parked foundation. It is not a completed Townlight product, and the Townlight Windows release does not install or support it. Examples and package names in the repository describe the foundation. Do not use them as suite installation instructions.</p>
        {links([("Released Windows suite, current modules and limits", suite), ("Current Townlight products", "/#products")])}
      </div>
      <div class="landing-panel">
        <h3>What it does not do</h3>
        <p>{escape(p['limits'])}</p>
      </div>
    </div>
  </section>
  <section class="landing-section" aria-labelledby="technical">
    <div class="landing-wrap">
      <div class="eyebrow">For technical teams</div>
      <h2 id="technical">Inspect the foundation.</h2>
      <p class="section-intro">Read the source and the parked notice in the repository. Code is AGPL-3.0. Documentation is CC BY 4.0.</p>
      {links([("Repository", repository), ("README and parked notice", f"{repository}#readme")])}
    </div>
  </section>"""
    nav = [("Products", "/#products"), ("Released suite", suite), ("Source", repository)]
    return page(f"{product} (parked foundation)", p["intro"], f"/products/{slug}/", suite, repository, body, nav)


def directory():
    groups = []
    for label, slugs in GROUPS:
        items = []
        for slug in slugs:
            product = PRODUCTS[slug]
            status = f' <span class="status">{escape(product["status"])}</span>' if "status" in product else ""
            items.append(
                f'<li>{link(product["name"], f"/products/{slug}/")}{status}'
                f'<p>{escape(product["short"])}</p></li>'
            )
        groups.append(
            f'<div class="directory-group"><h3>{escape(label)}</h3>'
            f'<ul class="directory-list">{"".join(items)}</ul></div>'
        )
    return "\n      ".join(groups)


def home_page():
    guide = "/manuals/suite.html"
    repository = "https://github.com/townlight/townlight"
    intro = "Run connected municipal workflows on a Windows installation your city controls. Keep original sources, staff decisions and approved records together."
    heading = hero(
        "Townlight / Windows public beta", "Municipal software cities can actually own.",
        intro, (f"Download Windows {VERSION}", MSI), ("Explore the products", "#products"),
        "A meeting decision, end to end",
        [
            ("Code → Meetings", "Bring a proposed ordinance to an agenda item with its source."),
            ("Meetings → Station", "Pair the proceedings with a recording through the configured media service."),
            ("Station → Records", "Preserve the original recording with a verifiable file identity."),
        ],
        "Signed Windows x64 installer · AGPL-3.0-only · Public beta",
        ("Start a records request", "/manuals/records.html#daily-workflow"),
    )
    release = release_notice("home", None)
    features = [
        ("Keep original evidence", "Use source links and original files to make the basis for a decision available for review."),
        ("Give staff the decision", "Use named staff actions, review steps and separate release copies to document what was approved."),
        ("Connect the record", "Carry meeting, ordinance and media context into the next workflow without losing its source."),
    ]
    body = f"""{heading}
{release}
  <section class="landing-section" id="products" aria-labelledby="product-title">
    <div class="landing-wrap">
      <div class="eyebrow">Product directory</div>
      <h2 id="product-title">Workspaces built around city work.</h2>
      <p class="section-intro">Explore the shipped workflows, operating guides and source for each component of the Windows beta.</p>
      {directory()}
      <p>Module status is tracked in the <a href="/versions.html#candidate-1.9.3.2">Windows 1.9.3.2 module inventory</a>; see the <a href="{ACCEPTANCE}">acceptance record</a>.</p>
    </div>
  </section>
  <div class="landing-band">
{capabilities(features, "A record you can trace.", "How the suite works")}
  </div>
  <section class="landing-section" aria-labelledby="evaluate">
    <div class="landing-wrap landing-split">
      <div>
        <div class="eyebrow">Start an evaluation</div>
        <h2 id="evaluate">Try one workflow with your team.</h2>
        <p>Install the signed Windows x64 beta, set up a test profile and choose a workflow from the suite manual. Use synthetic data first and commission city-specific sources, staff roles and equipment separately.</p>
        {links([("Suite manual", guide), ("First run", "/manuals/suite.html#first-run"), ("Technical specifications", "/manuals/suite.html#technical-specifications"), ("Records daily workflow", "/manuals/records.html#daily-workflow"), ("Windows staff access", "/manuals/windows-staff-workflows.html#staff-access"), ("Backup, recovery and maintenance", "/manuals/suite.html#backup-recovery-and-maintenance"), ("Verified workflows and limits", "/manuals/suite.html#verified-workflows-and-limits"), ("PDF manual", "/pdf/Townlight-Suite-Manual-Beta-1.pdf"), ("Word manual", "/docx/Townlight-Suite-Manual-Beta-1.docx"), ("Public announcement", "/announcement.html")])}
      </div>
      <div class="landing-panel">
        <h3>Release identity and evidence</h3>
        <p>Windows {VERSION} is the current public beta. See the release, checksums and acceptance record for current scope and limits.</p>
        {links([("Windows x64 MSI", MSI), ("Release and source catalog", RELEASE), ("SHA-256 checksums", CHECKSUMS), ("Acceptance and limits", ACCEPTANCE), ("Suite API", "/api/suite.html")])}
      </div>
    </div>
  </section>
  <section class="landing-section landing-band" aria-labelledby="portal">
    <div class="landing-wrap">
      <div class="eyebrow">Separate deployment</div>
      <h2 id="portal">A resident-facing portal.</h2>
      <p class="section-intro">Windows 1.9.2.1 historically documented sending explicitly approved packets and eligible Records releases to a separately deployed portal. The portal has its own deployment guide and release; see its historical acceptance.</p>
      {links([("Windows 1.9.2.1 acceptance", "https://github.com/townlight/townlight/releases/download/townlight-windows-v1.9.2.1/ACCEPTANCE-Windows-1.9.2.1.md"), ("Portal guide", "/manuals/portal.html"), ("Portal release", "https://github.com/townlight/townlight/releases/tag/townlight-beta-1-resident-portal")])}
    </div>
  </section>"""
    return page("Townlight | Municipal software cities can own", intro, "/", guide, repository, body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="*", help="home or product slugs. Default: all.")
    parser.add_argument("--check", action="store_true", help="Check that generated files match source.")
    args = parser.parse_args()
    for slug in args.pages or ["home", *PRODUCTS, *PARKED]:
        if slug == "home":
            path, html = SITE / "index.html", home_page()
        elif slug in PRODUCTS:
            path, html = SITE / "products" / slug / "index.html", product_page(slug)
        elif slug in PARKED:
            path, html = SITE / "products" / slug / "index.html", parked_page(slug)
        else:
            parser.error(f"Unknown landing page: {slug}")
        if args.check:
            if path.read_text(encoding="utf-8") != html:
                raise SystemExit(f"Regenerate {path.relative_to(SITE)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8", newline="\n")
        print(path.relative_to(SITE))


if __name__ == "__main__":
    main()
