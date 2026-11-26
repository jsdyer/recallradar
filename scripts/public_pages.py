"""Build working, directly linkable views of the tool from its page template."""
from html import escape
import json
import re

from search_metadata import add_search_metadata


def vehicle_preview(snapshot, vehicle):
    rows = [row for row in snapshot["rows"] if row.get("org") == "TC" and not row.get("archived") and any(
        f"{make} {model}" == vehicle for make, model, year in row.get("transport", {}).get("vehicles", [])
    )]
    lines = []
    for row in rows[:4]:
        years = sorted({str(year) for make, model, year in row["transport"]["vehicles"]
                        if f"{make} {model}" == vehicle and year})
        label = escape(row["title"])
        if row.get("url"):
            label = f'<a href="{escape(row["url"], quote=True)}">{label}</a>'
        lines.append("<li>" + label + " · listed model years " + escape(", ".join(years) or "unspecified") + "</li>")
    date = (snapshot.get("retrievedAt") or snapshot["built"])[:10]
    heading = f"{len(rows)} matching notices in the {date} snapshot."
    return "<p>" + heading + "</p>" + ("<ul>" + "".join(lines) + "</ul>" if lines else "")


def publish_pages(stage, page, tool, snapshot):
    cases = json.loads((stage / "use-cases.json").read_text(encoding="utf-8"))
    for case in cases:
        filename = case["slug"] + ".html"
        preset = {**tool, "title": case["title"], "url": tool["url"] + filename,
                  "description": case["description"]}
        title = escape(case["title"])
        summary = escape(case["description"])
        result = re.sub(r"<title>.*?</title>", lambda _: "<title>" + title + " · CoolCode</title>", page, count=1)
        result = re.sub(r"(<h1\b[^>]*>).*?</h1>", lambda m: m[1] + title + "</h1>", result, count=1, flags=re.S)
        result = re.sub(r'<meta name="description" content="[^"]*">', lambda _: '<meta name="description" content="' + summary + '">', result, count=1)
        result = re.sub(r"<body(?=[ >])", lambda _: '<body data-' + case["setting"] + '="' + escape(case["value"]) + '"', result, count=1)
        result = result.replace("<!-- case-context -->", '<p class="case-context">' + summary + ' <a href="./">Open the full tool</a></p>')
        result = result.replace('<div id="items"></div>', '<div id="items">' + vehicle_preview(snapshot, case["value"]) + '</div>')
        (stage / filename).write_text(add_search_metadata(result, preset), encoding="utf-8")
    (stage / "index.html").write_text(add_search_metadata(page, tool), encoding="utf-8")
