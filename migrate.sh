#!/usr/bin/env bash

set -e

# Database migration hook for the charm (paas-charm) deployment.
#
# Under the charm, ./entrypoint is not used: paas-charm launches gunicorn
# directly and runs this script once, on a single unit, before the web service
# starts. It is the only place schema migrations happen in that deployment.
#
# `flask db upgrade` is idempotent, so it is safe across restarts and multiple
# units. The DB URL is resolved by webapp.app (DATABASE_URL or the charm's
# POSTGRESQL_DB_CONNECT_STRING).
python3 -m flask --app webapp.app db upgrade
