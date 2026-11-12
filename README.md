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

### Authentication

Write endpoints (`POST`, `PUT`, `DELETE`) require a bearer token. Users must be on the product's
`owner_launchpad_team` or on the `products-api-admins` Launchpad team; creating products is admin-only.

To get a token, open `http://localhost:8040/login` in a browser and sign in with Canonical SSO. The
response contains an `access_token` that is valid for 1 hour. Send it on write requests:

```bash
curl -X PUT localhost:8040/products/<slug> \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" -d '{"name": "New name"}'
```

Tokens are signed with `SECRET_KEY`, so changing it invalidates all issued tokens.

Put the secrets in the untracked `.env.local` file (never in `.env`):

```bash
SSO_CLIENT_ID=...
SSO_CLIENT_SECRET=...
FLASK_DIRECTORY_API_TOKEN=...
```

Set `FLASK_DISABLE_AUTH_FOR_TESTS=true` to bypass authentication locally (the test suite sets this automatically).

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

On Linux, `DATABASE_URL` in `.env` uses `localhost`.

On macOS and Windows, Docker networking can behave differently. If the API
cannot connect to Postgres, create a local override file `.env.local` and set:

```bash
DATABASE_URL=postgresql://postgres:pw@host.docker.internal:5433/products_db
```

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

On Linux, `TEST_DATABASE_URL` in `.env` uses `localhost`.

On macOS and Windows, Docker networking can behave differently. If tests cannot
connect to Postgres, create a local override file `.env.local` and set:

```bash
TEST_DATABASE_URL=postgresql://postgres:pw@host.docker.internal:5433/test_products_db
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
