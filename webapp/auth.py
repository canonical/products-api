"""
DRAFT / TEMPLATE — not wired into app.py yet.

SSO via Canonical Identity Platform (OIDC), with authorization gated by
Launchpad team membership on the specific product being modified.

Pattern adapted from canonical/cs.canonical.com's webapp/sso.py, which
combines authlib-based OIDC login with a Launchpad team check. See that
repo for the more complete reference (it also does directory lookups to
resolve a user's Launchpad ID from their SSO email).

TODOs before this is real:
- Confirm how to get a user's Launchpad ID after OIDC login. C-IDP's
  token claims may already include it; if not, this needs the same
  directory-lookup step cs.canonical.com does.
- Wire these decorators onto the actual routes in app.py, per the spec:
  most POST/PUT/DELETE endpoints need `product_owner_required`; some
  (e.g. POST /products, creating a brand-new product with no existing
  owner) will need separate handling since there's no owner to check yet.
- Requires SSO_CLIENT_ID / SSO_CLIENT_SECRET / SSO_PROVIDER to be set
  once the Concordia OIDC ticket is fulfilled.
"""

import functools
import os

import flask
import requests
from authlib.integrations.flask_client import OAuth

from webapp.models import Product

LAUNCHPAD_API_URL = "https://api.launchpad.net/1.0"

DISABLE_SSO = os.environ.get("FLASK_DISABLE_AUTH_FOR_TESTS")


def init_sso(app: flask.Flask):
    oauth = OAuth(app)

    oauth.register(
        "canonical",
        client_id=os.getenv("SSO_CLIENT_ID"),
        client_secret=os.getenv("SSO_CLIENT_SECRET"),
        server_metadata_url=os.getenv("SSO_PROVIDER"),
        client_kwargs={
            "token_endpoint_auth_method": "client_secret_post",
            "scope": "openid profile email",
        },
    )

    @app.route("/login")
    def login():
        if "openid" in flask.session:
            return flask.redirect(flask.request.args.get("next") or "/")

        redirect_uri = flask.url_for("oauth_callback", _external=True)
        return oauth.canonical.authorize_redirect(redirect_uri)

    @app.route("/auth/callback")
    def oauth_callback():
        token = oauth.canonical.authorize_access_token()
        userinfo = token["userinfo"]

        flask.session["openid"] = {
            "email": userinfo["email"],
            "fullname": userinfo["name"],
            # TODO: resolve this properly, see module docstring
            "launchpad_id": None,
        }

        return flask.redirect(flask.request.args.get("next") or "/")


def _get_launchpad_teams(launchpad_id: str) -> list[str]:
    response = requests.get(
        f"{LAUNCHPAD_API_URL}/~{launchpad_id}/super_teams"
    )
    response.raise_for_status()
    return [team["name"] for team in response.json().get("entries", [])]


def product_owner_required(func):
    """Require the logged-in user to be on the owning team for the
    product identified by the `product_slug` URL argument.
    """

    @functools.wraps(func)
    def wrapper(product_slug, *args, **kwargs):
        if DISABLE_SSO:
            return func(product_slug, *args, **kwargs)

        identity = flask.session.get("openid")
        if not identity:
            return (
                flask.jsonify(
                    {"error": {"message": "Authentication required"}}
                ),
                401,
            )

        product = Product.query.filter_by(slug=product_slug).first()
        if not product:
            return (
                flask.jsonify({"error": {"message": "Product not found"}}),
                404,
            )

        if not product.owner_launchpad_team:
            return (
                flask.jsonify(
                    {"error": {"message": "Product has no owner set"}}
                ),
                403,
            )

        teams = _get_launchpad_teams(identity["launchpad_id"])
        if product.owner_launchpad_team not in teams:
            return flask.jsonify({"error": {"message": "Forbidden"}}), 403

        return func(product_slug, *args, **kwargs)

    return wrapper
