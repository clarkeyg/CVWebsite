"""Crawler-facing endpoints: /robots.txt and /sitemap.xml.

Both are generated per-request from the host the site is actually served on,
so nothing here hardcodes a domain and the same code works on localhost, a
staging host and production. ProxyFix in app.py means request.url_root already
reflects the real scheme/host from the reverse proxy.

Set SITE_BASE_URL to override (e.g. to force the canonical apex domain when the
app also answers on a www or internal hostname).
"""

import os
from datetime import date

from flask import Response, request

_HERE = os.path.dirname(os.path.abspath(__file__))

# Public, indexable pages. changefreq/priority are hints only — search engines
# largely ignore them, but they cost nothing and some crawlers still read them.
# Paths are relative to the site root; the file backing each one supplies lastmod.
_PAGES = [
    ("/", "templates/index.html", "monthly", "1.0"),
    ("/GTC/", "gtc/index.html", "weekly", "1.0"),
    ("/GTC/demo/cafe/", "gtc/demo/cafe/index.html", "monthly", "0.5"),
    ("/OptiFuelUK/", "optifueluk/index.html", "monthly", "0.8"),
    ("/OptiFuelUK/features.html", "optifueluk/features.html", "monthly", "0.6"),
    ("/OptiFuelUK/faq.html", "optifueluk/faq.html", "monthly", "0.6"),
]


def base_url():
    """Absolute site root, no trailing slash (e.g. "https://example.com")."""
    configured = (os.environ.get("SITE_BASE_URL") or "").strip()
    if configured:
        return configured.rstrip("/")
    return request.url_root.rstrip("/")


def _lastmod(relpath):
    """ISO date a page's source file last changed; today's date if unknown."""
    try:
        mtime = os.path.getmtime(os.path.join(_HERE, relpath))
    except OSError:
        return date.today().isoformat()
    return date.fromtimestamp(mtime).isoformat()


def _robots():
    """robots.txt — allow the public site, keep /stats and the form POST out."""
    root = base_url()
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        # The analytics dashboard is unauthenticated; useful to us, noise in an
        # index, and it would leak traffic figures into search results.
        "Disallow: /stats",
        "Disallow: /GTC/contact",
        "",
        "Sitemap: {0}/sitemap.xml".format(root),
        "",
    ])
    return Response(body, mimetype="text/plain")


def _sitemap():
    """sitemap.xml listing the public pages, with lastmod from file mtimes."""
    root = base_url()
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, source, changefreq, priority in _PAGES:
        out.append("  <url>")
        out.append("    <loc>{0}{1}</loc>".format(root, path))
        out.append("    <lastmod>{0}</lastmod>".format(_lastmod(source)))
        out.append("    <changefreq>{0}</changefreq>".format(changefreq))
        out.append("    <priority>{0}</priority>".format(priority))
        out.append("  </url>")
    out.append("</urlset>")
    return Response("\n".join(out) + "\n", mimetype="application/xml")


def init_app(app):
    """Wire the crawler endpoints into a Flask app."""
    app.add_url_rule("/robots.txt", "robots_txt", _robots)
    app.add_url_rule("/sitemap.xml", "sitemap_xml", _sitemap)
