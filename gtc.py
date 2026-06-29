"""GTC Development marketing site — static serving + contact-form backend.

Serves the static site under ./gtc at /GTC/ (mirroring the OptiFuelUK section),
and handles the "free mockup" contact form at POST /GTC/contact:

  * Stores each enquiry as a row in a local SQLite database (gitignored), so no
    lead is ever lost even if email delivery is unconfigured or fails.
  * Emails the enquiry to CONTACT_TO via SMTP when SMTP_* is configured;
    degrades gracefully (lead still stored) when it isn't.
  * Anti-spam without cookies or third parties: a hidden honeypot field, strict
    server-side validation, and a per-IP rate limit. As with analytics.py, the
    raw IP is never stored — only a daily-salted hash, used solely to rate-limit.

Configuration (environment variables):
  GTC_DB         Path to the SQLite file (default: ./gtc.db).
  CONTACT_TO     Where enquiries are emailed (default: clarkegeorge0509@gmail.com).
  CONTACT_FROM   From address for the email (default: SMTP_USER or CONTACT_TO).
  SMTP_HOST      SMTP server host. Unset => email disabled (leads still stored).
  SMTP_PORT      SMTP port (default: 587).
  SMTP_USER      SMTP username (used for login and as the default From).
  SMTP_PASSWORD  SMTP password / app password.
  SMTP_STARTTLS  Use STARTTLS (default: true). Accepts 1/true/yes.
"""

import hashlib
import os
import re
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.message import EmailMessage

from flask import current_app, jsonify, request, send_from_directory

_HERE = os.path.dirname(os.path.abspath(__file__))
GTC_DIR = os.path.join(_HERE, "gtc")
DB_PATH = os.environ.get("GTC_DB", os.path.join(_HERE, "gtc.db"))

DEFAULT_CONTACT_TO = "clarkegeorge0509@gmail.com"

# Per-IP rate limit for the contact form.
_RATE_LIMIT = 5          # max submissions ...
_RATE_WINDOW = 3600      # ... per this many seconds (1 hour)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #
def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db():
    with _connect() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS leads (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                ts       INTEGER NOT NULL,
                name     TEXT,
                business TEXT,
                email    TEXT,
                message  TEXT,
                ip_hash  TEXT,
                emailed  INTEGER NOT NULL DEFAULT 0
            )"""
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_leads_iphash_ts ON leads(ip_hash, ts)")


def _ip_hash():
    """Daily-salted, non-reversible hash of the client IP (never store raw IPs).

    Salt = the app SECRET_KEY (stable across the process) + today's date, so the
    hash is consistent within a day for rate-limiting but can't be used to track
    a visitor across days or be reversed back to an IP.
    """
    ip = request.remote_addr or ""
    day = datetime.now(timezone.utc).date().isoformat()
    salt = os.environ.get("SECRET_KEY", "gtc") + day
    return hashlib.sha256((salt + "|" + ip).encode()).hexdigest()[:16]


def _rate_limited(ip_hash):
    since = int(datetime.now(timezone.utc).timestamp()) - _RATE_WINDOW
    with _connect() as c:
        n = c.execute(
            "SELECT COUNT(*) FROM leads WHERE ip_hash=? AND ts>=?", (ip_hash, since)
        ).fetchone()[0]
    return n >= _RATE_LIMIT


# --------------------------------------------------------------------------- #
# Email
# --------------------------------------------------------------------------- #
def _send_email(lead):
    """Email the enquiry. Returns True if sent, False if email is unconfigured.

    Raises on an actual SMTP failure so the caller can log it; the lead is
    already stored regardless.
    """
    host = os.environ.get("SMTP_HOST")
    if not host:
        return False

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    use_tls = os.environ.get("SMTP_STARTTLS", "true").lower() in ("1", "true", "yes")
    to_addr = os.environ.get("CONTACT_TO", DEFAULT_CONTACT_TO)
    from_addr = os.environ.get("CONTACT_FROM", user or to_addr)

    subject = "New GTC mockup request — " + (lead["business"] or lead["name"] or "website enquiry")
    body = (
        "New enquiry from the GTC Development contact form:\n\n"
        "Name:     {name}\n"
        "Business: {business}\n"
        "Email:    {email}\n\n"
        "Message:\n{message}\n".format(
            name=lead["name"] or "—",
            business=lead["business"] or "—",
            email=lead["email"] or "—",
            message=lead["message"] or "—",
        )
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    if lead["email"]:
        msg["Reply-To"] = lead["email"]
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=10) as s:
        if use_tls:
            s.starttls()
        if user and password:
            s.login(user, password)
        s.send_message(msg)
    return True


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
def _index():
    """GTC Development landing page."""
    return send_from_directory(GTC_DIR, "index.html")


def _static(filename):
    """Serve GTC pages and assets (site.css, site.js, assets/...).

    Also serves the demo sites under gtc/demo/ (e.g. demo/cafe/site.css), since
    the path converter matches the nested path. The bare demo directory URL
    (no trailing index) is handled by its own route below.
    """
    return send_from_directory(GTC_DIR, filename)


def _cafe_demo():
    """Maple Street café — an example site linked from the GTC "Work" section."""
    return send_from_directory(os.path.join(GTC_DIR, "demo", "cafe"), "index.html")


def _contact():
    """Handle a contact-form submission: validate, store, email."""
    f = request.form

    # Honeypot: real browsers never fill the hidden "website" field. Pretend
    # success so bots don't learn they were caught, but drop the submission.
    if (f.get("website") or "").strip():
        return jsonify(ok=True)

    name = (f.get("name") or "").strip()[:120]
    business = (f.get("business") or "").strip()[:120]
    email = (f.get("email") or "").strip()[:200]
    message = (f.get("message") or "").strip()[:4000]

    if not name:
        return jsonify(ok=False, error="Please add your name."), 400
    if not _EMAIL_RE.match(email):
        return jsonify(ok=False, error="Please enter a valid email address."), 400

    ip_hash = _ip_hash()
    if _rate_limited(ip_hash):
        return (
            jsonify(ok=False, error="You've sent a few messages already — please email me directly at " + DEFAULT_CONTACT_TO + "."),
            429,
        )

    with _connect() as c:
        cur = c.execute(
            "INSERT INTO leads (ts, name, business, email, message, ip_hash) VALUES (?,?,?,?,?,?)",
            (int(datetime.now(timezone.utc).timestamp()), name, business, email, message, ip_hash),
        )
        lead_id = cur.lastrowid

    lead = {"name": name, "business": business, "email": email, "message": message}
    try:
        if _send_email(lead):
            with _connect() as c:
                c.execute("UPDATE leads SET emailed=1 WHERE id=?", (lead_id,))
    except Exception as exc:  # email failed, but the lead is safely stored
        current_app.logger.warning("GTC contact: email delivery failed for lead %s: %s", lead_id, exc)

    return jsonify(ok=True)


def init_app(app):
    """Wire the GTC Development site into a Flask app: DB, static routes, form."""
    _init_db()
    app.add_url_rule("/GTC/", "gtc_index", _index)
    app.add_url_rule("/GTC/contact", "gtc_contact", _contact, methods=["POST"])
    # Demo index routes (with/without trailing slash) take precedence over the
    # catch-all below; the demo's own assets fall through to _static.
    app.add_url_rule("/GTC/demo/cafe/", "gtc_demo_cafe", _cafe_demo)
    app.add_url_rule("/GTC/demo/cafe", "gtc_demo_cafe_noslash", _cafe_demo)
    app.add_url_rule("/GTC/<path:filename>", "gtc_static", _static)
