#!/usr/bin/env bash

set -e

# Database migration hook for the 12-factor (paas-charm) deployment.
#
# Why this file was added:
#   When deployed as a charm, the repo's ./entrypoint is NOT executed.
#   paas-charm owns the workload lifecycle and launches gunicorn directly via
#   Pebble, which bypasses the `flask db upgrade` step baked into ./entrypoint.
#
# Why it is needed:
#   paas-charm runs a dedicated migration script (lookup precedence: migrate,
#   migrate.sh, migrate.py, manage.py) once, on a single unit, after the
#   database relation is available and before the web service starts. Without
#   this file, schema migrations would never run under the charm and the app
#   would start against an un-migrated database and fail.
#
# `flask db upgrade` is idempotent: re-running it when already at the latest
# revision is a no-op, so it is safe across restarts and multiple units. The DB
# URL is resolved by webapp.app (DATABASE_URL or the charm-injected
# POSTGRESQL_DB_CONNECT_STRING).
python3 -m flask --app webapp.app db upgrade
