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

The app trusts `X-Forwarded-Proto` / `X-Forwarded-Host` from one proxy hop
(`ProxyFix` in [`app.py`](app.py)), so run it behind nginx (or similar) with a
production WSGI server rather than the Flask dev server:

```bash
pip install gunicorn
gunicorn --bind 127.0.0.1:5000 app:app
```

Set `SECRET_KEY` in the host environment and leave `FLASK_DEBUG` unset.

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
