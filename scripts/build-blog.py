#!/usr/bin/env python3
"""Build the static blog pages in /blogg from the Markdown files in /blogg-kilde.

Each source file starts with a small front matter block:

    ---
    tittel: "..."
    metabeskrivelse: "..."
    publisert: "2026-10-17"        (optional, defaults to DEFAULT_DATE)
    foreslått_url: "cloud247.no/blogg/<slug>"
    canonical: "https://..."       (optional, when the original lives elsewhere: the blog
                                    card then links there and /blogg/<slug> redirects to it)
    ---

Usage:  pip install markdown pymdown-extensions && python3 scripts/build-blog.py
Writes blogg/<slug>.html (served as /blogg/<slug>), blogg/index.html and sitemap.xml.
"""

import html
import json
import math
import re
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "blogg-kilde"
OUT = ROOT / "blogg"
SITE = "https://cloud247.no"
DEFAULT_DATE = "2026-10-17"
ASSET_VERSION = "20261017-blogg"

MONTHS = ["januar", "februar", "mars", "april", "mai", "juni", "juli",
          "august", "september", "oktober", "november", "desember"]


def norsk_dato(iso):
    d = date.fromisoformat(iso)
    return f"{d.day}. {MONTHS[d.month - 1]} {d.year}"


def parse_front_matter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("missing front matter")
    meta = {}
    for line in match.group(1).splitlines():
        m = re.match(r'^([^\s:][^:]*):\s*"?(.*?)"?\s*$', line)
        if m and m.group(2):
            meta[m.group(1).strip()] = m.group(2)
    return meta, text[match.end():]


def esc(value):
    return html.escape(value, quote=True)


def render_body(md_text):
    # The page hero shows the title: drop the first H1 and anything above it (e.g. a breadcrumb line)
    h1 = re.search(r"^# .*\n+", md_text, flags=re.M)
    if h1:
        md_text = md_text[h1.end():]
    # Notes in HTML comments (sources, reminders) stay in the Markdown only
    md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.S)
    # List items indented with three spaces ("1. ") need four for Python-Markdown
    md_text = re.sub(r"^   (?! )", "    ", md_text, flags=re.M)
    body = markdown.markdown(md_text, extensions=["tables", "pymdownx.superfences", "sane_lists"])
    # Keep links to our own blog relative, so they work on any host
    body = body.replace(f'href="{SITE}/blogg/', 'href="/blogg/')
    # Relative guide links in posts written for the DMARC site point there
    body = body.replace('href="/guider/', 'href="https://dmarc.cloud247.no/guider/')
    # Wide tables scroll sideways on phones instead of stretching the page
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    # FAQ entries ("**Question?**" followed by the answer) get the answer on its own line
    body = re.sub(r"(<p><strong>(?:(?!</strong>).)*\?</strong>)\n", r"\1<br>\n", body)
    # The closing call to action (last paragraph, "**Question?** ... [link](...)") gets its own box
    start = body.rfind("<p>")
    last = body[start:]
    if re.match(r"<p><strong>(?:(?!</strong>).)*\?</strong>", last) and last.rstrip().endswith("</p>"):
        last = re.sub(r"</a>\.</p>$", "</a></p>", last.rstrip())  # no stray full stop after the button
        body = body[:start] + f'<aside class="post-cta">{last}</aside>\n'
    # ...or a closing section ("## Heading", text, and a paragraph with just the link)
    elif re.fullmatch(r"<p><a [^>]+>[^<]+</a></p>", last.strip()):
        section = body.rfind("<h2")
        body = body[:section] + f'<aside class="post-cta">{body[section:].rstrip()}</aside>\n'
    return body


def read_minutes(md_text):
    words = len(re.findall(r"\w+", md_text))
    return max(1, math.ceil(words / 200))


def header():
    return """  <header class="site-header">
    <div class="shell header-inner">
      <a class="brand" href="/" aria-label="Cloud247">
        <img src="/assets/cloud247-logo.svg" alt="Cloud247 Technology">
      </a>
      <nav class="site-nav" aria-label="Hovedmeny">
        <a href="/">Verkt&oslash;y</a>
        <a href="/blogg/" aria-current="{current}">Blogg</a>
      </nav>
    </div>
  </header>"""


def footer():
    return """  <footer class="site-footer">
    <div class="shell footer-inner">
      <span>&copy; <span id="year"></span> Cloud247</span>
      <span class="footer-links"><a href="/">Cloud Toolbox</a><a href="/blogg/">Blogg</a></span>
    </div>
  </footer>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>"""


def head(title, description, url, og_type, ld, extra=""):
    return f"""<!doctype html>
<html lang="nb">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{url}">
  <meta name="theme-color" content="#061A2F">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="{og_type}">
  <meta property="og:url" content="{url}">
  <meta property="og:site_name" content="Cloud247">
  <meta property="og:locale" content="nb_NO">
  <meta name="twitter:card" content="summary">{extra}
  <link rel="icon" href="/assets/cloud247-mark.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
  <link rel="stylesheet" href="/styles.css?v={ASSET_VERSION}">
  <link rel="stylesheet" href="/blogg/blogg.css?v={ASSET_VERSION}">
  <script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=2)}
  </script>
</head>"""


ORG = {"@type": "Organization", "@id": f"{SITE}/#organization", "name": "Cloud247",
       "url": f"{SITE}/", "logo": f"{SITE}/assets/cloud247-logo.svg"}


def load_posts():
    posts = []
    for path in SRC.glob("*.md"):
        meta, md_text = parse_front_matter(path.read_text(encoding="utf-8"))
        slug = meta.get("foreslått_url", "").rstrip("/").split("/")[-1] or path.stem
        posts.append({
            "slug": slug,
            "title": meta["tittel"],
            "description": meta["metabeskrivelse"],
            "published": meta.get("publisert", DEFAULT_DATE),
            "canonical": meta.get("canonical", f"{SITE}/blogg/{slug}"),
            "md": md_text,
        })
    # Newest first
    posts.sort(key=lambda p: (p["published"], p["slug"]), reverse=True)
    return posts


def is_external(post):
    return post["canonical"] != f"{SITE}/blogg/{post['slug']}"


def post_href(post):
    return post["canonical"] if is_external(post) else f"/blogg/{post['slug']}"


def post_card(post, heading="h2", featured=False):
    css = "post-card is-featured" if featured else "post-card"
    return f"""        <article class="{css}">
          <p class="post-meta"><time datetime="{post['published']}">{norsk_dato(post['published'])}</time> &middot; {read_minutes(post['md'])} min lesing</p>
          <{heading}><a href="{esc(post_href(post))}">{esc(post['title'])}</a></{heading}>
          <p>{esc(post['description'])}</p>
          <a class="post-card-link" href="{esc(post_href(post))}" aria-hidden="true" tabindex="-1">{'Les guiden' if is_external(post) else 'Les innlegget'} <span>&rarr;</span></a>
        </article>"""


def build_redirect(post):
    """The text lives elsewhere: /blogg/<slug> only forwards there, so old links keep working."""
    target = esc(post["canonical"])
    page = f"""<!doctype html>
<html lang="nb">
<head>
  <meta charset="utf-8">
  <title>{esc(post['title'])} | Cloud247</title>
  <link rel="canonical" href="{target}">
  <meta http-equiv="refresh" content="0; url={target}">
  <script>location.replace({json.dumps(post['canonical'])});</script>
</head>
<body>
  <p>Innlegget har flyttet til <a href="{target}">{target}</a>.</p>
</body>
</html>
"""
    (OUT / f"{post['slug']}.html").write_text(page, encoding="utf-8")


def build_post(post, others):
    url = f"{SITE}/blogg/{post['slug']}"
    canonical = post["canonical"]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": post["title"], "description": post["description"],
         "datePublished": post["published"], "dateModified": post["published"], "inLanguage": "nb",
         "url": canonical, "mainEntityOfPage": canonical, "author": ORG, "publisher": ORG},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Cloud Toolbox", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Blogg", "item": f"{SITE}/blogg/"},
            {"@type": "ListItem", "position": 3, "name": post["title"], "item": url}]},
    ]}
    extra = f'\n  <meta property="article:published_time" content="{post["published"]}">'
    related = "\n".join(post_card(p, "h3") for p in others)
    page = f"""{head(post['title'] + ' | Cloud247', post['description'], canonical, 'article', ld, extra)}
<body>
{header().replace('{current}', 'false')}

  <main>
    <section class="blog-hero post-hero">
      <div class="shell post-shell">
        <nav class="breadcrumb" aria-label="Br&oslash;dsmuler"><a href="/">Cloud Toolbox</a> <span aria-hidden="true">/</span> <a href="/blogg/">Blogg</a></nav>
        <h1>{esc(post['title'])}</h1>
        <p class="post-meta"><time datetime="{post['published']}">{norsk_dato(post['published'])}</time> &middot; {read_minutes(post['md'])} min lesing &middot; Cloud247</p>
      </div>
    </section>

    <article class="post-body">
      <div class="shell post-shell prose">
{render_body(post['md'])}
      </div>
    </article>

    <section class="related" aria-labelledby="related-title">
      <div class="shell">
        <h2 id="related-title">Flere innlegg</h2>
        <div class="post-grid">
{related}
        </div>
      </div>
    </section>
  </main>

{footer()}
</body>
</html>
"""
    (OUT / f"{post['slug']}.html").write_text(page, encoding="utf-8")


def build_index(posts):
    url = f"{SITE}/blogg/"
    description = "Praktiske guider om e-postsikkerhet, DMARC, SPF, MTA-STS og Microsoft Intune fra Cloud247."
    ld = {"@context": "https://schema.org", "@type": "Blog", "name": "Cloud247 Blogg", "url": url,
          "description": description, "inLanguage": "nb", "publisher": ORG,
          "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": p["canonical"],
                        "datePublished": p["published"]} for p in posts]}
    # With an odd number of posts the newest one spans both columns, so the grid has no gap
    cards = "\n".join(post_card(p, featured=(i == 0 and len(posts) % 2 == 1)) for i, p in enumerate(posts))
    page = f"""{head('Blogg | Cloud247', description, url, 'website', ld)}
<body>
{header().replace('{current}', 'page')}

  <main>
    <section class="blog-hero">
      <div class="shell">
        <p class="eyebrow">CLOUD247 BLOGG</p>
        <h1>Blogg</h1>
        <p class="lead">Praktiske guider om e-postsikkerhet, DMARC, SPF, MTA-STS og Microsoft Intune &ndash; skrevet for IT-ansvarlige og MSP-er.</p>
      </div>
    </section>

    <section class="blog-list" aria-label="Innlegg">
      <div class="shell">
        <div class="post-grid">
{cards}
        </div>
      </div>
    </section>
  </main>

{footer()}
</body>
</html>
"""
    (OUT / "index.html").write_text(page, encoding="utf-8")


def build_sitemap(posts):
    newest = max(p["published"] for p in posts)
    urls = [(f"{SITE}/", newest), (f"{SITE}/blogg/", newest)]
    # Posts whose canonical lives elsewhere are left out of this site's sitemap
    urls += [(p["canonical"], p["published"]) for p in posts if not is_external(p)]
    entries = "\n".join(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{mod}</lastmod>\n  </url>" for loc, mod in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n',
        encoding="utf-8")


def main():
    posts = load_posts()
    OUT.mkdir(exist_ok=True)
    for post in posts:
        if is_external(post):
            build_redirect(post)
        else:
            build_post(post, [p for p in posts if p is not post][:3])
    build_index(posts)
    build_sitemap(posts)
    print(f"Built {len(posts)} posts: " + ", ".join(p["slug"] for p in posts))


if __name__ == "__main__":
    main()
