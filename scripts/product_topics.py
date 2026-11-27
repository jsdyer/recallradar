"""Publish consumer topic results using the category labels in the Canadian recall export."""
from html import escape
from urllib.parse import urlencode
from xml.etree import ElementTree as ET
import json

BASE = "https://coolcode.ca/recallradar/"
SOURCE = "https://recalls-rappels.canada.ca/en"
LIMIT = 12


def topic_matches(row, label):
    return label in [value.strip() for value in row.get("category", "").split(" - ")]


def link(url, label):
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def render(path, title, description, content):
    url = BASE + path
    depth = "../" * path.count("/")
    return f'''<!doctype html>
<html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Recall Radar</title><meta name="description" content="{escape(description,quote=True)}">
<link rel="canonical" href="{url}"><meta property="og:title" content="{escape(title,quote=True)}">
<meta property="og:description" content="{escape(description,quote=True)}"><meta property="og:url" content="{url}">
<link rel="stylesheet" href="{depth}style.css"><script defer src="/assets/tool-metrics.js" referrerpolicy="no-referrer"></script>
</head><body data-tool-id="recallradar"><a class="skip" href="#main">Skip to notices</a>
<header><div class="wrap">{link(depth,"Recall Radar")}{link("https://coolcode.ca/","CoolCode.ca")}</div></header>
<main class="wrap" id="main"><h1 class="topic-title">{escape(title)}</h1><p>{escape(description)}</p>{content}</main>
<footer class="wrap">{link(SOURCE,"Government of Canada recalls and safety alerts")} · {link("https://coolcode.ca/report/?tool=recallradar","Report an issue")}</footer>
</body></html>'''


def publish_topics(stage, snapshot):
    topics = json.loads((stage / "product-topics.json").read_text())
    if len({t["slug"] for t in topics}) != len(topics) or len({t["label"] for t in topics}) != len(topics):
        raise ValueError("Duplicate recall topic")
    directory = stage / "records"
    directory.mkdir()
    paths = ["records/"]
    entries = []
    date = (snapshot.get("retrievedAt") or snapshot["built"])[:10]
    date_note = ("Snapshot retrieved " if snapshot.get("retrievedAt") else "Snapshot built ") + date + "."
    options = []
    for topic in topics:
        label, slug = topic["label"], topic["slug"]
        options.append(f'<option value="{escape(slug,quote=True)}">{escape(label)}</option>')
        rows = [r for r in snapshot["rows"] if topic_matches(r, label)]
        current = [r for r in rows if not r.get("archived")]
        archived = len(rows) - len(current)
        title = f"Canadian recalls and safety alerts for {label.lower()}"
        description = f"Check notices filed under {label.lower()} in the Canadian recall data. Open the official notice for affected models, lot numbers and instructions."
        search = "../../?" + urlencode({"category": slug}) + "#search-title"
        body = (f'<p>{len(current):,} non-archived notices · {archived:,} archived. {escape(date_note)}</p>'
                f'<p>{link(search, "Search these notices by product or brand")} · {link("../","Browse all product topics")}</p>'
                '<section class="panel"><h2>Recently updated notices</h2>')
        if current:
            body += f"<p>Showing {min(len(current),LIMIT)} of {len(current):,} non-archived notices, ordered by the source’s last update.</p><ul>"
            for row in current[:LIMIT]:
                issue = escape(row.get("issue") or "")
                updated = escape(row.get("updated") or "Date unavailable")
                body += f'<li class="topic-item">{link(row["url"],row["title"])}<br><span class="muted">{updated}'+(" · "+issue if issue else "")+"</span></li>"
            body += "</ul>"
        else:
            body += "<p>This snapshot contains no non-archived notices in this category. You can include archived notices in the search.</p>"
        body += ('</section><p>The publisher can assign a notice to several categories. '
                 'A missing match or an archive flag cannot establish whether a particular product is safe. '
                 'Use the model or lot number and the instructions in the official notice.</p>')
        topic_dir = directory / slug
        topic_dir.mkdir()
        (topic_dir / "index.html").write_text(render(f"records/{slug}/",title,description,body),encoding="utf-8")
        entries.append(f'<li class="topic-item">{link("./"+slug+"/",label)} · {len(current):,} non-archived notices · {archived:,} archived</li>')
        if rows:
            paths.append(f"records/{slug}/")
    description = "Choose a product category to see recently updated Canadian recalls and safety alerts, then search within that category by product or brand."
    body = (f'<p>{escape(date_note)} Each group uses the category in the federal source. A notice can appear in several groups.</p>'
            +'<ul class="panel topic-index">'+''.join(entries)+'</ul><p>'+link("../#query","Search every product and vehicle notice")+"</p>")
    (directory / "index.html").write_text(render("records/","Canadian consumer product recall topics",description,body),encoding="utf-8")
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for path in paths:
        ET.SubElement(ET.SubElement(sitemap,"url"),"loc").text = BASE+path
    (stage / "sitemap.xml").write_bytes(ET.tostring(sitemap,encoding="utf-8",xml_declaration=True))
    return "".join(options)
