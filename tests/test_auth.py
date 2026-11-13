import unittest
from unittest import mock

import requests

import webapp.auth as auth
from tests import BaseTestCase
from webapp.helpers import DirectoryAPIError, get_user_from_directory_by_key


class AuthTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        patch = mock.patch.object(auth, "_auth_disabled", return_value=False)
        patch.start()
        self.addCleanup(patch.stop)
        self.models["product"].owner_launchpad_team = "owners"
        self.db.session.commit()
        self.token = auth.issue_access_token("user", "a@b.c")

    def put_product(self, teams=None, side_effect=None, token=None):
        headers = {"Authorization": f"Bearer {token or self.token}"}
        with mock.patch.object(
            auth,
            "_get_launchpad_teams",
            return_value=teams,
            side_effect=side_effect,
        ):
            return self.client.put(
                "/products/test-product",
                json={"name": "Renamed"},
                headers=headers,
            )


class TestProductOwnerRequired(AuthTestCase):
    def test_missing_authorization_header_gets_401(self):
        response = self.client.put(
            "/products/test-product", json={"name": "Renamed"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Bearer", response.headers["WWW-Authenticate"])

    def test_tampered_token_gets_401(self):
        response = self.put_product(teams=["owners"], token=self.token + "x")
        self.assertEqual(response.status_code, 401)

    def test_expired_token_gets_401(self):
        with mock.patch.object(auth.time, "time", return_value=0):
            expired = auth.issue_access_token("user", "a@b.c")
        response = self.put_product(teams=["owners"], token=expired)
        self.assertEqual(response.status_code, 401)

    def test_non_owner_gets_403(self):
        self.assertEqual(self.put_product(teams=["other"]).status_code, 403)

    def test_owner_is_allowed(self):
        self.assertEqual(self.put_product(teams=["owners"]).status_code, 200)

    def test_teams_are_looked_up_for_token_subject(self):
        with mock.patch.object(
            auth, "_get_launchpad_teams", return_value=["owners"]
        ) as get_teams:
            self.client.put(
                "/products/test-product",
                json={"name": "Renamed"},
                headers={"Authorization": f"Bearer {self.token}"},
            )
        get_teams.assert_called_once_with("user")

    def test_admin_is_allowed_on_product_without_owner(self):
        self.models["product"].owner_launchpad_team = None
        self.db.session.commit()
        response = self.put_product(teams=[auth.AUTH_ADMIN_TEAM])
        self.assertEqual(response.status_code, 200)

    def test_launchpad_failure_returns_503(self):
        response = self.put_product(
            side_effect=requests.ConnectionError("down")
        )
        self.assertEqual(response.status_code, 503)


class TestAdminRequired(AuthTestCase):
    def test_non_admin_cannot_create_product(self):
        with mock.patch.object(
            auth, "_get_launchpad_teams", return_value=["owners"]
        ):
            response = self.client.post(
                "/products",
                json={
                    "name": "New Product",
                    "deployments": [{"name": "Snap", "artifact_type": "snap"}],
                },
                headers={"Authorization": f"Bearer {self.token}"},
            )
        self.assertEqual(response.status_code, 403)


class TestOAuthCallback(BaseTestCase):
    def callback(self, employees):
        sso_token = {"userinfo": {"email": "Jo@canonical.com"}}
        with mock.patch(
            "authlib.integrations.flask_client.apps.FlaskOAuth2App"
            ".authorize_access_token",
            return_value=sso_token,
        ), mock.patch.object(
            auth, "get_user_from_directory_by_key", return_value=employees
        ):
            return self.client.get("/auth/callback")

    def test_returns_one_hour_bearer_token_for_exact_email_match(self):
        response = self.callback(
            [
                {"email": "xjo@canonical.com", "launchpadId": "wrong"},
                {"email": "jo@canonical.com", "launchpadId": "jo"},
            ]
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["token_type"], "Bearer")
        self.assertEqual(payload["expires_in"], 3600)
        claims = auth.decode_access_token(payload["access_token"])
        self.assertEqual(claims["sub"], "jo")
        self.assertEqual(claims["exp"] - claims["iat"], 3600)

    def test_user_without_launchpad_id_gets_403(self):
        response = self.callback([{"email": "jo@canonical.com"}])
        self.assertEqual(response.status_code, 403)


class TestAuthDisabledFlag(unittest.TestCase):
    def test_false_string_does_not_disable_auth(self):
        with mock.patch.dict(
            "os.environ",
            {
                "DISABLE_AUTH_FOR_TESTS": "false",
                "FLASK_DISABLE_AUTH_FOR_TESTS": "false",
            },
        ):
            self.assertFalse(auth._auth_disabled())


class TestGetLaunchpadTeams(unittest.TestCase):
    @mock.patch("webapp.auth.requests.get")
    def test_follows_pagination(self, get):
        get.return_value.json.side_effect = [
            {"entries": [{"name": "a"}], "next_collection_link": "next"},
            {"entries": [{"name": "b"}]},
        ]
        self.assertEqual(auth._get_launchpad_teams("user"), ["a", "b"])
        self.assertEqual(get.call_count, 2)


class TestDirectoryLookup(unittest.TestCase):
    def test_rejects_unknown_filter_key(self):
        with self.assertRaises(ValueError):
            get_user_from_directory_by_key("name) { id } #", "x")

    @mock.patch.dict("os.environ", {"DIRECTORY_API_TOKEN": "token"})
    @mock.patch("webapp.helpers.requests.post")
    def test_request_failure_raises_directory_error(self, post):
        post.side_effect = requests.ConnectionError("down")
        with self.assertRaises(DirectoryAPIError):
            get_user_from_directory_by_key("email", "a@b.c")


if __name__ == "__main__":
    unittest.main()
