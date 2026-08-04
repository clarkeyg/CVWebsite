"""Cache-busting URLs for CSS and JavaScript.

Browsers keep a static file for as long as its Cache-Control max-age allows and
will not re-request it before then, so a deploy can leave a returning visitor
running fresh HTML against a stale stylesheet. Stamping each asset URL with the
file's modification time changes the URL whenever the bytes change, which lets
the files be cached hard *and* still update the instant they are rebuilt.

Two ways in, because the two sites are served differently:

  * ``asset()`` is a Jinja global for templates/ (see templates/index.html).
  * ``resolve()`` expands ``%ASSET_V:<file>%`` sentinels in plain static HTML
    that never passes through Jinja (see gtc/index.html), matching the
    %SITE_BASE_URL% idiom already used there.
"""

import os
import re

from flask import request, url_for

_HERE = os.path.dirname(os.path.abspath(__file__))

# One year. Safe only for URLs carrying a ?v= stamp -- see init_app.
_IMMUTABLE = "public, max-age=31536000, immutable"

_SENTINEL = re.compile(r"%ASSET_V:([A-Za-z0-9_./-]+)%")


def stamp(*path_parts):
    """Modification time of a file below the app root, as an int.

    Returns 0 when the file is missing, so a typo in a path degrades to an
    unversioned URL rather than raising midway through rendering a page.
    """
    try:
        return int(os.stat(os.path.join(_HERE, *path_parts)).st_mtime)
    except OSError:
        return 0


def asset(filename):
    """url_for('static') plus a ?v= stamp, e.g. /static/css/style.css?v=1785832532."""
    version = stamp("static", *filename.split("/"))
    url = url_for("static", filename=filename)
    return "{}?v={}".format(url, version) if version else url


def resolve(html, *root_parts):
    """Expand %ASSET_V:<file>% sentinels in html against the given directory.

    Lets hand-written static HTML use cache-busting URLs without a template
    engine: ``site.css?v=%ASSET_V:site.css%`` becomes ``site.css?v=1785832532``.
    """
    return _SENTINEL.sub(
        lambda m: str(stamp(*root_parts, *m.group(1).split("/"))), html
    )


def init_app(app):
    """Expose asset() to templates and cache stamped assets for a year.

    The long max-age is applied by response header rather than by config so it
    lands only on requests that actually carry a stamp, whichever route served
    them -- Flask's /static/ endpoint or the GTC send_from_directory route.
    HTML is excluded outright: a stray ?v= on a page URL must never pin a year
    of caching to a document that changes on every deploy.
    """
    app.jinja_env.globals["asset"] = asset

    @app.after_request
    def _cache_stamped_assets(response):
        if (
            request.args.get("v")
            and response.status_code == 200
            and not response.mimetype.startswith("text/html")
        ):
            response.headers["Cache-Control"] = _IMMUTABLE
        return response

    return app
