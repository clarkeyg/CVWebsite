from flask import Flask, render_template, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import secrets

import analytics
import gtc

app = Flask(__name__)

# Trust X-Forwarded-For/Proto/Host from the reverse proxy in front of the app, so
# generated URLs use https in production and analytics sees the real client IP.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configuration
# Set SECRET_KEY in the host environment for sessions that survive restarts;
# otherwise fall back to a random per-process key so no real secret is committed.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Cookieless first-party analytics: records page views and serves /stats.
# See analytics.py. Set STATS_PASSWORD to enable the dashboard.
analytics.init_app(app)

# GTC Development marketing site at /GTC/ (static site + contact-form backend).
# See gtc.py. Set SMTP_* to have enquiries emailed; leads are stored either way.
gtc.init_app(app)


@app.route('/')
def index():
    """Main portfolio page. All content lives in templates/index.html."""
    return render_template('index.html')


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
