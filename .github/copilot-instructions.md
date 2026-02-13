# Copilot instructions (products-api)

## Big picture
- This is a Flask API built on Canonical’s `canonicalwebteam.flask-base` with a single app package at [webapp/app.py](webapp/app.py).
- The WSGI entrypoint is [wsgi.py](wsgi.py), intended for Gunicorn in production.

## Key workflows
- Local development uses `dotrun`. The scripts are defined in [package.json](package.json):
	- `dotrun install` to install dependencies.
	- `dotrun serve` (or `dotrun`) to run the API.

## Conventions and patterns
- Create the Flask app via `FlaskBase` in [webapp/app.py](webapp/app.py).
- New API routes should follow the `/v1/...` prefix (see `/v1/health`).
- Keep app code inside the `webapp` package; WSGI remains thin in [wsgi.py](wsgi.py).

## Dependencies and integrations
- Python dependencies live in [requirements.txt](requirements.txt), including `canonicalwebteam.flask-base`, `Talisker`, and `gunicorn`.
- `dotrun` expects `.venv/` and `.dotrun.json` to remain untracked (see [.gitignore](.gitignore)).

## Primary references
- Project overview and setup: [README.md](README.md)
- App entrypoint: [webapp/app.py](webapp/app.py)
- WSGI entrypoint: [wsgi.py](wsgi.py)
