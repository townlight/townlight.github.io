"""Render the landing pages for the existing branch-based GitHub Pages site."""

import argparse
import json
from html import escape
from pathlib import Path

from content import GROUPS, PRODUCTS

SITE = Path(__file__).resolve().parent.parent
VERSION = "1.7.2.1"
TAG = f"townlight-windows-v{VERSION}"
RELEASE = f"https://github.com/townlight/townlight/releases/tag/{TAG}"
ASSETS = f"https://github.com/townlight/townlight/releases/download/{TAG}"
MSI = f"{ASSETS}/Townlight-Windows-x64-{VERSION}.msi"
ACCEPTANCE = f"{ASSETS}/ACCEPTANCE-Windows-{VERSION}.md"
PINS = json.loads((SITE / f"reference/windows-{VERSION}-source-pins.json").read_text(encoding="utf-8"))
PUBLIC_SITE = "https://townlight.github.io"


def link(label, url, css_class=None):
    classes = f' class="{escape(css_class)}"' if css_class else ""
    return f'<a href="{escape(url)}"{classes}>{escape(label)}</a>'


def links(items):
    return '<ul class="landing-link-list">' + "".join(
        f"<li>{link(label, url)}</li>" for label, url in items
    ) + "</ul>"


def actions(primary, secondary):
    return '<div class="actions">' + link(*primary, "button primary") + link(*secondary, "button") + "</div>"


def page(title, description, route, guide, repository, main):
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
        {link("Products", "/#products")}
        {link("Guide", guide)}
        {link("Download", RELEASE)}
        {link("Source", repository)}
      </nav>
    </div>
  </header>
  <main id="main">
{main}
  </main>
  <footer class="landing-footer">
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


def hero(eyebrow, headline, intro, primary, secondary, workflow_title, steps, release_line):
    return f"""  <section class="landing-hero" aria-labelledby="title">
    <div class="landing-wrap hero-layout">
      <div>
        <div class="eyebrow">{escape(eyebrow)}</div>
        <h1 id="title">{escape(headline)}</h1>
        <p class="hero-copy">{escape(intro)}</p>
        {actions(primary, secondary)}
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


def product_page(slug):
    p = PRODUCTS[slug]
    guide = f"/manuals/{slug}.html"
    repository = f"https://github.com/townlight/{p['repo']}"
    pin = PINS["repositories"][p["repo"]]["commit"]
    status = p.get("status", "Windows public beta")
    product = f"Townlight {p['name']}"
    heading = hero(
        f"{product} / {p['category']}", p["headline"], p["intro"],
        ("Read the operating guide", guide), ("View Windows release", RELEASE),
        p["workflow"], p["steps"], f"{status} · Townlight {VERSION} · AGPL-3.0-only",
    )
    diagram = ""
    if p.get("diagram"):
        diagram = f"""
      <details>
        <summary>View the {escape(p['name'])} architecture diagram</summary>
        <img class="landing-diagram" loading="lazy" src="/assets/{p['diagram']}-architecture.svg"
          alt="{escape(product)} architecture. The operating guide describes the services and workflow in text.">
      </details>"""
    body = f"""{heading}
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
      {links([("Released component source", f"{repository}/tree/{pin}"), ("API reference", f"/api/{slug}.html"), ("Repository and contributions", repository)])}
{diagram}
    </div>
  </section>"""
    return page(product, p["intro"], f"/products/{slug}/", guide, repository, body)


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
    )
    features = [
        ("Keep original evidence", "Use source links and original files to make the basis for a decision available for review."),
        ("Give staff the decision", "Use named staff actions, review steps and separate release copies to document what was approved."),
        ("Connect the record", "Carry meeting, ordinance and media context into the next workflow without losing its source."),
    ]
    body = f"""{heading}
  <section class="landing-section" id="products" aria-labelledby="product-title">
    <div class="landing-wrap">
      <div class="eyebrow">Product directory</div>
      <h2 id="product-title">Workspaces built around city work.</h2>
      <p class="section-intro">Explore the shipped workflows, operating guides and source for each component of the Windows beta.</p>
      {directory()}
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
        {links([("Suite manual", guide), ("PDF manual", "/pdf/Townlight-Suite-Manual-Beta-1.pdf"), ("Word manual", "/docx/Townlight-Suite-Manual-Beta-1.docx"), ("Public announcement", "/announcement.html")])}
      </div>
      <div class="landing-panel">
        <h3>Release identity and evidence</h3>
        <p>Windows {VERSION} updates the installer name and metadata. Its application payload is identical to 1.7.1.1. The release records the verified upgrade from 1.7.1.1, along with the scope of reused functional evidence.</p>
        {links([("Release, source and checksums", RELEASE), ("Acceptance and limits", ACCEPTANCE), ("Suite API", "/api/suite.html")])}
      </div>
    </div>
  </section>
  <section class="landing-section landing-band" aria-labelledby="portal">
    <div class="landing-wrap">
      <div class="eyebrow">Separate deployment</div>
      <h2 id="portal">A resident-facing portal.</h2>
      <p class="section-intro">The portal beta provides a city-facing website for published material. Follow its own deployment guide and release instructions.</p>
      {links([("Portal guide", "/manuals/portal.html"), ("Portal release", "https://github.com/townlight/townlight/releases/tag/townlight-beta-1-resident-portal")])}
    </div>
  </section>"""
    return page("Townlight | Municipal software cities can own", intro, "/", guide, repository, body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="*", help="home or product slugs. Default: all.")
    parser.add_argument("--check", action="store_true", help="Check that generated files match source.")
    args = parser.parse_args()
    for slug in args.pages or ["home", *PRODUCTS]:
        if slug == "home":
            path, html = SITE / "index.html", home_page()
        elif slug in PRODUCTS:
            path, html = SITE / "products" / slug / "index.html", product_page(slug)
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
