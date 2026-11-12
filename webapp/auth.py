import functools
import time

import flask
import requests
from authlib.integrations.base_client import OAuthError
from authlib.integrations.flask_client import OAuth
from canonicalwebteam.flask_base.env import get_flask_env
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import OctKey

from webapp.helpers import DirectoryAPIError, get_user_from_directory_by_key
from webapp.models import Product

LAUNCHPAD_API_URL = "https://api.launchpad.net/1.0"
LAUNCHPAD_TIMEOUT = 10
AUTH_ADMIN_TEAM = "products-api-admins"

TOKEN_ALGORITHM = "HS256"
TOKEN_ISSUER = "products-api"
TOKEN_AUDIENCE = "products-api"
TOKEN_EXPIRY_SECONDS = int(get_flask_env("TOKEN_EXPIRY_SECONDS") or 3600)


def _auth_disabled() -> bool:
    value = get_flask_env("DISABLE_AUTH_FOR_TESTS") or ""
    if value.strip().lower() not in ("1", "true", "yes", "on"):
        return False
    return flask.current_app.testing or flask.current_app.debug


def _signing_key() -> OctKey:
    return OctKey.import_key(flask.current_app.config["SECRET_KEY"])


def issue_access_token(launchpad_id: str, email: str) -> str:
    now = int(time.time())
    claims = {
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
        "sub": launchpad_id,
        "email": email,
        "iat": now,
        "exp": now + TOKEN_EXPIRY_SECONDS,
    }
    return jwt.encode(
        {"alg": TOKEN_ALGORITHM},
        claims,
        _signing_key(),
        algorithms=[TOKEN_ALGORITHM],
    )


def decode_access_token(token: str) -> dict:
    """Verify signature, issuer, audience and expiry.

    Raises JoseError if the token is invalid or expired.
    """
    decoded = jwt.decode(token, _signing_key(), algorithms=[TOKEN_ALGORITHM])
    jwt.JWTClaimsRegistry(
        iss={"essential": True, "value": TOKEN_ISSUER},
        aud={"essential": True, "value": TOKEN_AUDIENCE},
        sub={"essential": True},
        exp={"essential": True},
    ).validate(decoded.claims)
    return decoded.claims


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
        redirect_uri = flask.url_for("oauth_callback", _external=True)
        return oauth.canonical.authorize_redirect(redirect_uri)

    @app.route("/auth/callback")
    def oauth_callback():
        try:
            sso_token = oauth.canonical.authorize_access_token()
        except OAuthError:
            flask.abort(401, description="SSO authentication failed.")

        userinfo = sso_token.get("userinfo") or {}
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

        launchpad_id = user_data.get("launchpadId")
        if not launchpad_id:
            flask.abort(
                403, description="No Launchpad account linked to this user."
            )

        response = flask.jsonify(
            {
                "access_token": issue_access_token(launchpad_id, email),
                "token_type": "Bearer",
                "expires_in": TOKEN_EXPIRY_SECONDS,
            }
        )
        response.headers["Cache-Control"] = "no-store"
        return response


def _get_launchpad_teams(launchpad_id: str) -> list[str]:
    """Return the names of all teams the Launchpad user participates in.

    Raises requests.RequestException if Launchpad cannot be queried.
    """
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

    return teams


def _error(message: str, status: int):
    response = flask.jsonify({"error": {"message": message}})
    if status == 401:
        response.headers["WWW-Authenticate"] = (
            f'Bearer realm="{TOKEN_AUDIENCE}"'
        )
    return response, status


def _authenticate():
    """Return (claims, None) for a valid bearer token, or (None, error)."""
    scheme, _, token = flask.request.headers.get(
        "Authorization", ""
    ).partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None, _error("Authentication required", 401)

    try:
        return decode_access_token(token.strip()), None
    except JoseError:
        return None, _error("Invalid or expired token", 401)


def _get_teams(claims):
    """Return (teams, None) for the token's user, or (None, error)."""
    try:
        return _get_launchpad_teams(claims["sub"]), None
    except requests.RequestException:
        return None, _error("Unable to verify team membership", 503)


def product_owner_required(func):
    """Require a bearer token for a user on the owning team for the
    product identified by the `product_slug` URL argument, or on
    the admin team.
    """

    @functools.wraps(func)
    def wrapper(product_slug, *args, **kwargs):
        if _auth_disabled():
            return func(product_slug, *args, **kwargs)

        claims, error = _authenticate()
        if error:
            return error

        product = Product.query.filter_by(slug=product_slug).first()
        if not product:
            return _error("Product not found", 404)

        teams, error = _get_teams(claims)
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
    """Require a bearer token for a user on the admin team."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if _auth_disabled():
            return func(*args, **kwargs)

        claims, error = _authenticate()
        if error:
            return error

        teams, error = _get_teams(claims)
        if error:
            return error

        if AUTH_ADMIN_TEAM not in teams:
            return _error("Forbidden", 403)

        return func(*args, **kwargs)

    return wrapper
