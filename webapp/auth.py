import functools
import time
from urllib.parse import urlparse

import flask
import requests
from authlib.integrations.base_client import OAuthError
from authlib.integrations.flask_client import OAuth
from canonicalwebteam.flask_base.env import get_flask_env

from webapp.helpers import DirectoryAPIError, get_user_from_directory_by_key
from webapp.models import Product

LAUNCHPAD_API_URL = "https://api.launchpad.net/1.0"
LAUNCHPAD_TIMEOUT = 10
TEAMS_CACHE_TTL = 300
AUTH_ADMIN_TEAM = "products-api-admins"

_teams_cache: dict[str, tuple[float, list[str]]] = {}


def _auth_disabled() -> bool:
    value = get_flask_env("DISABLE_AUTH_FOR_TESTS") or ""
    return value.strip().lower() in ("1", "true", "yes", "on")


def _safe_next_url(url: str | None) -> str:
    """Only allow same-site relative redirects, to avoid open redirects."""
    if not url:
        return "/"
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc or not url.startswith("/"):
        return "/"
    if url.startswith("//") or "\\" in url:
        return "/"
    return url


def init_sso(app: flask.Flask):
    oauth = OAuth(app)

    oauth.register(
        "canonical",
        client_id=get_flask_env("SSO_CLIENT_ID"),
        client_secret=get_flask_env("SSO_CLIENT_SECRET"),
        server_metadata_url=get_flask_env("SSO_CLIENT_URI"),
        client_kwargs={
            "token_endpoint_auth_method": "client_secret_post",
            "scope": "openid profile email",
        },
    )

    @app.route("/login")
    def login():
        next_url = _safe_next_url(flask.request.args.get("next"))
        if "openid" in flask.session:
            return flask.redirect(next_url)

        flask.session["login_next"] = next_url
        redirect_uri = flask.url_for("oauth_callback", _external=True)
        return oauth.canonical.authorize_redirect(redirect_uri)

    @app.route("/auth/callback")
    def oauth_callback():
        try:
            token = oauth.canonical.authorize_access_token()
        except OAuthError:
            flask.abort(401, description="SSO authentication failed.")

        userinfo = token.get("userinfo") or {}
        email = userinfo.get("email")
        if not email:
            flask.abort(401, description="SSO did not return an email.")

        try:
            employees = get_user_from_directory_by_key("email", email)
        except DirectoryAPIError:
            flask.abort(503, description="Directory lookup failed.")

        # The directory filter is a substring match, so require exact email
        user_data = next(
            (
                employee
                for employee in employees
                if (employee.get("email") or "").lower() == email.lower()
            ),
            None,
        )
        if user_data is None:
            flask.abort(404, description="User not found in directory.")

        flask.session["openid"] = {
            "email": email,
            "fullname": userinfo.get("name"),
            "launchpad_id": user_data.get("launchpadId"),
        }

        return flask.redirect(
            _safe_next_url(flask.session.pop("login_next", None))
        )


def _get_launchpad_teams(launchpad_id: str) -> list[str]:
    """Return the names of all teams the Launchpad user participates in.

    Results are cached per user for TEAMS_CACHE_TTL seconds.
    Raises requests.RequestException if Launchpad cannot be queried.
    """
    cached = _teams_cache.get(launchpad_id)
    if cached and cached[0] > time.monotonic():
        return cached[1]

    teams = []
    url = f"{LAUNCHPAD_API_URL}/~{launchpad_id}/super_teams"
    params = {"ws.size": 300}
    while url:
        response = requests.get(url, params=params, timeout=LAUNCHPAD_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        teams.extend(team["name"] for team in payload.get("entries", []))
        # next_collection_link already includes the paging query params
        url = payload.get("next_collection_link")
        params = None

    _teams_cache[launchpad_id] = (time.monotonic() + TEAMS_CACHE_TTL, teams)
    return teams


def _error(message: str, status: int):
    return flask.jsonify({"error": {"message": message}}), status


def _current_user_teams():
    """Return (teams, None) for the logged-in user, or (None, error)."""
    identity = flask.session.get("openid")
    if not identity:
        return None, _error("Authentication required", 401)

    launchpad_id = identity.get("launchpad_id")
    if not launchpad_id:
        return None, _error("No Launchpad account linked to this user", 403)

    try:
        return _get_launchpad_teams(launchpad_id), None
    except requests.RequestException:
        return None, _error("Unable to verify team membership", 503)


def product_owner_required(func):
    """Require the logged-in user to be on the owning team for the
    product identified by the `product_slug` URL argument, or on
    the admin team.
    """

    @functools.wraps(func)
    def wrapper(product_slug, *args, **kwargs):
        if _auth_disabled():
            return func(product_slug, *args, **kwargs)

        if not flask.session.get("openid"):
            return _error("Authentication required", 401)

        product = Product.query.filter_by(slug=product_slug).first()
        if not product:
            return _error("Product not found", 404)

        teams, error = _current_user_teams()
        if error:
            return error

        if AUTH_ADMIN_TEAM in teams:
            return func(product_slug, *args, **kwargs)

        if not product.owner_launchpad_team:
            return _error("Product has no owner set", 403)

        if product.owner_launchpad_team not in teams:
            return _error("Forbidden", 403)

        return func(product_slug, *args, **kwargs)

    return wrapper


def admin_required(func):
    """Require the logged-in user to be on the admin team."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if _auth_disabled():
            return func(*args, **kwargs)

        teams, error = _current_user_teams()
        if error:
            return error

        if AUTH_ADMIN_TEAM not in teams:
            return _error("Forbidden", 403)

        return func(*args, **kwargs)

    return wrapper
