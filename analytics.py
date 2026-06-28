"""Lightweight, cookieless, first-party analytics for the CV site.

Logs one row per HTML page view to a local SQLite database via an after_request
hook, and serves a password-protected /stats dashboard.

Privacy by design:
  * No cookies, no cross-site tracking, no third parties.
  * Raw IPs are never stored. The IP is used transiently to (a) look up a
    country (if a GeoIP DB is configured) and (b) build a unique-visitor hash
    salted with a secret that rotates every day, then it is discarded. The
    daily salt makes the hash non-reversible and prevents tracking across days.

Configuration (environment variables):
  STATS_PASSWORD  Enables and protects /stats (Basic auth). Unset => dashboard off.
  STATS_USER      Username for /stats (default: "admin").
  ANALYTICS_DB    Path to the SQLite file (default: ./analytics.db).
  GEOIP_DB        Path to a MaxMind GeoLite2-Country.mmdb (optional, for countries).
"""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from flask import Response, request, render_template

_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("ANALYTICS_DB", os.path.join(_HERE, "analytics.db"))

# Optional GeoIP — degrades gracefully to "Unknown" when unavailable.
_geo_reader = None
try:  # pragma: no cover - depends on optional package + data file
    import geoip2.database

    _geo_path = os.environ.get("GEOIP_DB", os.path.join(_HERE, "GeoLite2-Country.mmdb"))
    if os.path.exists(_geo_path):
        _geo_reader = geoip2.database.Reader(_geo_path)
except Exception:
    _geo_reader = None


# --------------------------------------------------------------------------- #
# Database helpers
# --------------------------------------------------------------------------- #
def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db():
    with _connect() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS views (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                ts      INTEGER NOT NULL,
                day     TEXT    NOT NULL,
                hour    INTEGER NOT NULL,
                path    TEXT,
                ref     TEXT,
                country TEXT,
                browser TEXT,
                os      TEXT,
                device  TEXT,
                visitor TEXT
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_views_ts ON views(ts)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_views_day ON views(day)")
        c.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")


def _daily_salt(day):
    """Random per-day salt, persisted so unique counts survive restarts."""
    key = "salt:" + day
    with _connect() as c:
        row = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        if row:
            return row["value"]
        c.execute("INSERT OR IGNORE INTO meta(key, value) VALUES(?, ?)", (key, secrets.token_hex(16)))
        # prune salts older than ~3 days
        c.execute("DELETE FROM meta WHERE key LIKE 'salt:%' AND key < ?", ("salt:" + (datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat(),))
        row = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"]


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
def _parse_ua(ua):
    ua = ua or ""
    if re.search(r"iPad|Tablet", ua):
        device = "Tablet"
    elif re.search(r"Mobi|Android|iPhone|iPod", ua):
        device = "Mobile"
    else:
        device = "Desktop"

    if "iPhone" in ua or "iPad" in ua or "iPod" in ua:
        os_name = "iOS"
    elif "Mac OS X" in ua:
        os_name = "macOS"
    elif "Windows" in ua:
        os_name = "Windows"
    elif "Android" in ua:
        os_name = "Android"
    elif "Linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Other"

    if "Edg" in ua:
        browser = "Edge"
    elif "OPR" in ua or "Opera" in ua:
        browser = "Opera"
    elif "Firefox" in ua:
        browser = "Firefox"
    elif "Chrome" in ua:
        browser = "Chrome"
    elif "Safari" in ua:
        browser = "Safari"
    else:
        browser = "Other"
    return browser, os_name, device


_BOT_RE = re.compile(
    r"bot|crawl|spider|slurp|bingpreview|facebookexternalhit|embedly|quora|"
    r"pinterest|headless|phantom|curl|wget|python-requests|httpx|monitor|uptime|probe",
    re.I,
)


def _referrer_host(host_self):
    ref = request.referrer or ""
    if not ref:
        return "Direct"
    try:
        netloc = urlparse(ref).netloc.lower()
    except Exception:
        return "Direct"
    if not netloc:
        return "Direct"
    netloc = netloc.split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    if host_self and netloc == host_self.split(":")[0].lower():
        return "Internal"
    return netloc


def _country(ip):
    if not ip:
        return "Unknown"
    if ip.startswith(("127.", "10.", "192.168.", "::1", "fc", "fd")) or ip.startswith("172.16."):
        return "Local"
    if not _geo_reader:
        return "Unknown"
    try:
        return _geo_reader.country(ip).country.name or "Unknown"
    except Exception:
        return "Unknown"


# --------------------------------------------------------------------------- #
# Recording
# --------------------------------------------------------------------------- #
def _record(response):
    try:
        if request.method != "GET" or response.status_code != 200:
            return response
        if not (response.content_type or "").startswith("text/html"):
            return response
        path = request.path
        if path.startswith("/static") or path.startswith("/stats") or path == "/favicon.ico":
            return response
        ua = request.headers.get("User-Agent", "")
        # Count real browsers only. Health checks, uptime monitors and HTTP
        # libraries send either no User-Agent or a non-browser one (curl,
        # Go-http-client, okhttp, …); every real browser's UA contains "Mozilla".
        # This filters out the kind of every-30s monitor traffic that otherwise
        # dwarfs genuine visits. _BOT_RE still catches Mozilla-spoofing crawlers.
        if "Mozilla" not in ua or _BOT_RE.search(ua):
            return response

        now = datetime.now(timezone.utc)
        day = now.date().isoformat()
        ip = request.remote_addr or ""
        visitor = hashlib.sha256(("{}|{}|{}".format(_daily_salt(day), ip, ua)).encode()).hexdigest()[:16]
        browser, os_name, device = _parse_ua(ua)

        with _connect() as c:
            c.execute(
                "INSERT INTO views (ts, day, hour, path, ref, country, browser, os, device, visitor) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (int(now.timestamp()), day, now.hour, path, _referrer_host(request.host),
                 _country(ip), browser, os_name, device, visitor),
            )
    except Exception:
        pass  # analytics must never break the site
    return response


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
_RANGES = {"today": "Today", "7d": "Last 7 days", "30d": "Last 30 days", "all": "All time"}


def _since(rng):
    now = datetime.now(timezone.utc)
    if rng == "today":
        return int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    if rng == "7d":
        return int((now - timedelta(days=7)).timestamp())
    if rng == "30d":
        return int((now - timedelta(days=30)).timestamp())
    return 0


def _top(c, column, since, limit=8):
    rows = c.execute(
        "SELECT COALESCE(NULLIF({0}, ''), 'Unknown') AS k, COUNT(*) AS n "
        "FROM views WHERE ts >= ? GROUP BY k ORDER BY n DESC LIMIT ?".format(column),
        (since, limit),
    ).fetchall()
    mx = max((r["n"] for r in rows), default=0)
    return [{"label": r["k"], "n": r["n"], "pct": round(100 * r["n"] / mx) if mx else 0} for r in rows]


def _stats_view():
    pw = os.environ.get("STATS_PASSWORD")
    if not pw:
        return Response("Analytics dashboard is disabled. Set STATS_PASSWORD to enable it.", 503)
    user = os.environ.get("STATS_USER", "admin")
    auth = request.authorization
    if not auth or auth.username != user or not hmac.compare_digest(auth.password or "", pw):
        return Response("Authentication required.", 401, {"WWW-Authenticate": 'Basic realm="stats"'})

    rng = request.args.get("range", "30d")
    if rng not in _RANGES:
        rng = "30d"
    since = _since(rng)

    with _connect() as c:
        views = c.execute("SELECT COUNT(*) FROM views WHERE ts >= ?", (since,)).fetchone()[0]
        uniques = c.execute("SELECT COUNT(DISTINCT visitor) FROM views WHERE ts >= ?", (since,)).fetchone()[0]
        all_views = c.execute("SELECT COUNT(*) FROM views").fetchone()[0]
        today0 = _since("today")
        today_views = c.execute("SELECT COUNT(*) FROM views WHERE ts >= ?", (today0,)).fetchone()[0]

        pages = _top(c, "path", since)
        refs = _top(c, "ref", since)
        countries = _top(c, "country", since)
        browsers = _top(c, "browser", since)
        oses = _top(c, "os", since)
        devices = _top(c, "device", since)

        # 30-day daily trend
        day_rows = {r["day"]: r["n"] for r in c.execute(
            "SELECT day, COUNT(*) n FROM views WHERE ts >= ? GROUP BY day",
            (int((datetime.now(timezone.utc) - timedelta(days=29)).replace(hour=0, minute=0, second=0).timestamp()),),
        ).fetchall()}
        trend = []
        for i in range(29, -1, -1):
            d = (datetime.now(timezone.utc) - timedelta(days=i)).date().isoformat()
            trend.append({"day": d[5:], "n": day_rows.get(d, 0)})
        tmax = max((d["n"] for d in trend), default=0)
        for d in trend:
            d["pct"] = round(100 * d["n"] / tmax) if tmax else 0

        # hour-of-day histogram (within range)
        hour_rows = {r["hour"]: r["n"] for r in c.execute(
            "SELECT hour, COUNT(*) n FROM views WHERE ts >= ? GROUP BY hour", (since,)
        ).fetchall()}
        hmax = max(hour_rows.values(), default=0)
        hours = [{"h": h, "n": hour_rows.get(h, 0), "pct": round(100 * hour_rows.get(h, 0) / hmax) if hmax else 0} for h in range(24)]

        recent = c.execute(
            "SELECT ts, path, ref, country, browser, os, device FROM views ORDER BY ts DESC LIMIT 15"
        ).fetchall()
        recent = [
            {"when": datetime.fromtimestamp(r["ts"], timezone.utc).strftime("%d %b %H:%M"),
             "path": r["path"], "ref": r["ref"], "country": r["country"],
             "browser": r["browser"], "os": r["os"], "device": r["device"]}
            for r in recent
        ]

    return render_template(
        "stats.html", rng=rng, ranges=_RANGES, geo=bool(_geo_reader),
        views=views, uniques=uniques, all_views=all_views, today_views=today_views,
        pages=pages, refs=refs, countries=countries, browsers=browsers, oses=oses,
        devices=devices, trend=trend, hours=hours, recent=recent,
    )


def init_app(app):
    """Wire analytics into a Flask app: create tables, hook requests, add /stats."""
    _init_db()
    app.after_request(_record)
    app.add_url_rule("/stats", "stats", _stats_view)
