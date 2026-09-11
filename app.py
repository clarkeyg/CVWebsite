from flask import Flask, redirect, render_template, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import re
import secrets

import analytics
import assets
import gtc
import seo

app = Flask(__name__)

# Trust X-Forwarded-For/Proto/Host from the reverse proxy in front of the app, so
# generated URLs use https in production and analytics sees the real client IP.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configuration
# Set SECRET_KEY in the host environment for sessions that survive restarts;
# otherwise fall back to a random per-process key so no real secret is committed.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Version-stamped CSS/JS URLs, so a deploy is picked up immediately instead of
# waiting out a cached copy. Registered first: it adds the asset() template
# global the pages below render with. See assets.py.
assets.init_app(app)

# Cookieless first-party analytics: records page views and serves a public
# /stats dashboard (aggregate counts only). See analytics.py.
analytics.init_app(app)

# GTC Web Studio marketing site at /GTC/ (static site + contact-form backend).
# See gtc.py. Set SMTP_* to have enquiries emailed; leads are stored either way.
gtc.init_app(app)

# /robots.txt and /sitemap.xml, generated from the request host. See seo.py.
seo.init_app(app)

# The section prefixes are mixed-case but people type them in lowercase, and
# Flask routing is case-sensitive, so /gtc or /optifueluk would 404. Any casing
# of a prefix (as a whole path segment, so /gtcfoo is left alone) 301s to the
# canonical path, keeping the subpath and query string.
SECTION_PREFIXES = ('/GTC', '/OptiFuelUK')
_SECTION_RE = re.compile(
    '^(' + '|'.join(re.escape(p) for p in SECTION_PREFIXES) + ')(?=/|$)', re.IGNORECASE
)


@app.before_request
def canonical_section_case():
    """Redirect /gtc, /Gtc/site.css, /optifueluk?x=y etc. to their canonical casing."""
    m = _SECTION_RE.match(request.path)
    if not m or m.group(1) in SECTION_PREFIXES:
        return None
    prefix = next(p for p in SECTION_PREFIXES if p.lower() == m.group(1).lower())
    # Bare prefix goes straight to the trailing-slash form, not via a 2nd redirect.
    target = prefix + (request.path[m.end():] or '/')
    if request.query_string:
        target += '?' + request.query_string.decode('latin-1')
    return redirect(target, code=301)


@app.route('/')
def index():
    """Main portfolio page. All content lives in templates/index.html."""
    # base_url feeds the canonical/og:url tags and the Person structured data,
    # which need an absolute origin. See seo.py.
    return render_template('index.html', base_url=seo.base_url())


# ---- OptiFuelUK marketing site -------------------------------------------
# Static multi-page site served under /OptiFuelUK (files live in ./optifueluk).
# The trailing-slash route makes Flask redirect /OptiFuelUK -> /OptiFuelUK/,
# so the pages' relative links and assets resolve correctly.
OPTIFUEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'optifueluk')


@app.route('/OptiFuelUK/')
def optifueluk_index():
    """OptiFuelUK landing page."""
    return send_from_directory(OPTIFUEL_DIR, 'index.html')


@app.route('/OptiFuelUK/<path:filename>')
def optifueluk_static(filename):
    """Serve OptiFuelUK pages and assets (faq.html, site.css, assets/...)."""
    return send_from_directory(OPTIFUEL_DIR, filename)


if __name__ == '__main__':
    # debug defaults OFF; opt in locally with FLASK_DEBUG=1. Never enable in prod.
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    app.run(debug=debug, host='0.0.0.0', port=int(os.environ.get('PORT', '5000')))
