# CV Website

Personal portfolio site for **George Clarke**, plus the marketing site for
**[OptiFuelUK](https://apps.apple.com/gb/app/optifueluk/id6773123227)** served
from the same Flask app.

- **CV / portfolio**: a single-page site (hero, about, experience timeline,
  projects, contact) at `/`.
- **OptiFuelUK**: a static multi-page marketing site at `/OptiFuelUK/` for the
  iOS app that ranks UK petrol stations along your route by *true total cost*
  (fuel + the fuel burned on the detour).

Live at <https://github.com/clarkeyg/CVWebsite> · hosted privately behind a
reverse proxy.

## Tech stack

| Layer    | Choice                                              |
| -------- | --------------------------------------------------- |
| Backend  | Python 3.12, [Flask](https://flask.palletsprojects.com/) 3 |
| Frontend | Hand-written HTML/CSS/JS, [Font Awesome](https://fontawesome.com/) icons via CDN |
| Proxy    | Designed to sit behind nginx (uses Werkzeug `ProxyFix`) |

No build step, no frontend framework. Open the templates and edit.

## Project structure

```
.
├── app.py                       # Flask app: routes only
├── requirements.txt             # Pinned Python dependencies
├── .env.example                 # Documented environment variables
├── templates/
│   └── index.html               # CV page markup (styles & scripts in static/)
├── static/
│   ├── css/style.css            # Page styles
│   └── javascript/cv_website_main.js   # Nav, scroll progress, reveals
└── optifueluk/                  # Static OptiFuelUK marketing site
    ├── index.html  features.html  faq.html
    ├── site.css  site.js
    └── assets/   (app-icon.png, map-tile.png)
```

## Getting started

Requires Python 3.12+.

```bash
# 1. Clone
git clone https://github.com/clarkeyg/CVWebsite.git
cd CVWebsite

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) configure environment, see .env.example
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export FLASK_DEBUG=1               # local only

# 5. Run
python app.py
```

The site is then at <http://localhost:5000/> and OptiFuelUK at
<http://localhost:5000/OptiFuelUK/>.

## Configuration

All configuration is via environment variables (read directly from the
environment, so `.env` is **not** auto-loaded). See [`.env.example`](.env.example).

| Variable      | Default            | Purpose                                            |
| ------------- | ------------------ | -------------------------------------------------- |
| `SECRET_KEY`  | random per process | Flask session signing key. Set it so sessions survive restarts. |
| `FLASK_DEBUG` | off                | `1`/`true`/`yes` enables the debug server. Never in production. |
| `PORT`        | `5000`             | Port the app binds to.                             |

## Routes

| Method | Path                       | Description                          |
| ------ | -------------------------- | ------------------------------------ |
| GET    | `/`                        | CV / portfolio page                  |
| GET    | `/OptiFuelUK/`             | OptiFuelUK landing page              |
| GET    | `/OptiFuelUK/<path>`       | OptiFuelUK pages & assets            |

## Deployment

The site is designed to run **self-hosted behind a reverse proxy**: the app binds
to localhost, and the proxy terminates TLS and forwards to it.

```
Internet ──▶ nginx (TLS, HTTP/2) ──proxy_pass──▶ 127.0.0.1:5000 (this app)
```

The app trusts `X-Forwarded-Proto` / `X-Forwarded-Host` from one proxy hop
(`ProxyFix` in [`app.py`](app.py)), so generated URLs use HTTPS in production.

### 1. Run it with a production WSGI server

Use gunicorn, not the Flask/Werkzeug dev server (`python app.py`), in production:

```bash
pip install gunicorn
gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
```

### 2. Keep it running with systemd

Example unit (`/etc/systemd/system/cvwebsite.service`) — dedicated unprivileged
user, localhost bind, basic sandboxing:

```ini
[Unit]
Description=CV Website
After=network.target

[Service]
User=cvweb
Group=cvweb
WorkingDirectory=/srv/CVWebsite
Environment=SECRET_KEY=change-me
ExecStart=/srv/CVWebsite/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
Restart=on-failure
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/CVWebsite

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now cvwebsite
```

### 3. nginx reverse proxy

```nginx
server {
    listen 443 ssl;
    server_name example.com;
    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host  $host;
    }
}
server { listen 80; server_name example.com; return 301 https://$host$request_uri; }
```

### Production checklist

- [ ] Served by **gunicorn** (or similar) — never the Werkzeug dev server.
- [ ] Runs as a **dedicated non-root user**.
- [ ] App bound to **`127.0.0.1`** only; the proxy is the sole public entry point.
- [ ] `SECRET_KEY` set in the environment; `FLASK_DEBUG` unset.
- [ ] **TLS auto-renews** (e.g. certbot) so the cert can't silently expire.

### Deploying an update

```bash
cd /srv/CVWebsite && git pull
sudo systemctl restart cvwebsite      # picks up template/code changes
```

## Notes

- **No frontend build step.** Edit `templates/index.html` (markup),
  `static/css/style.css` (styling) and `static/javascript/cv_website_main.js`
  (behaviour) directly.
- **Two runtime CDNs** are used: Google Fonts (Inter) and Font Awesome (icons).
  They degrade gracefully offline; self-host them if you need the site to work
  fully air-gapped.

## License & use

Personal project. Code is public for reference; the CV content, branding, and
OptiFuelUK assets are not licensed for reuse.
