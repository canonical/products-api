# Products API

Centralized API for accessing release and support lifecycle information for all Canonical products.

## Why

Canonical products have different release cadences and support models. This API provides a single source of truth for release dates and support lifecycles.

## Local development

The simplest way to run the API locally is using dotrun:

```bash
docker-compose up -d
dotrun
```

Once the server has started, you can visit `http://0.0.0.0:8040/` in your browser.

After you close the server with `<ctrl>+c` you should run `docker-compose down` to stop the database.

## Prerequisites

- Docker
- Python 3.10+
- `dotrun` (see https://github.com/canonical/dotrun)

## Install dependencies

```bash
dotrun install
```

If you need to run migrations locally, use a host-local virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools==69.5.1
pip install -r requirements.txt
```

## Run the API

```bash
docker-compose up -d
dotrun serve
```

The API will start at `http://0.0.0.0:8040/` with a health endpoint at `/v1/health`.

## Database migrations (local)

Run migrations from the host virtualenv (not through `dotrun exec`):

```bash
source .venv/bin/activate
set -a && source .env && set +a
export FLASK_APP=webapp.app
docker-compose up -d postgres
flask db upgrade
```

Useful checks:

```bash
flask db current
flask db heads
```

Note: avoid `dotrun exec flask db ...` for local migrations, as that runtime may use a different network/path context than the host `.env` values.

## Testing

```bash
dotrun test
```

## Linting and formatting

```bash
dotrun lint-python  # Run linters
dotrun format-python  # Auto-format Python code
```

## Project layout

- `app.py` – WSGI entrypoint for production servers
- `webapp/app.py` – Flask application using `FlaskBase`
- `requirements.txt` – Python dependencies
- `package.json` – Node.js scripts and development tasks
