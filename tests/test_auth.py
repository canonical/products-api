import unittest
from unittest import mock

import requests

import webapp.auth as auth
from tests import BaseTestCase
from webapp.helpers import DirectoryAPIError, get_user_from_directory_by_key


class AuthTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        auth._teams_cache.clear()
        patches = [
            mock.patch.object(auth, "_auth_disabled", return_value=False),
            mock.patch.object(
                auth.flask,
                "session",
                {"openid": {"email": "a@b.c", "launchpad_id": "user"}},
            ),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.models["product"].owner_launchpad_team = "owners"
        self.db.session.commit()

    def put_product(self, teams=None, side_effect=None):
        with mock.patch.object(
            auth,
            "_get_launchpad_teams",
            return_value=teams,
            side_effect=side_effect,
        ):
            return self.client.put(
                "/products/test-product", json={"name": "Renamed"}
            )


class TestProductOwnerRequired(AuthTestCase):
    def test_anonymous_user_gets_401(self):
        auth.flask.session.clear()
        self.assertEqual(self.put_product(teams=[]).status_code, 401)

    def test_user_without_launchpad_id_gets_403(self):
        auth.flask.session["openid"]["launchpad_id"] = None
        self.assertEqual(self.put_product(teams=["owners"]).status_code, 403)

    def test_non_owner_gets_403(self):
        self.assertEqual(self.put_product(teams=["other"]).status_code, 403)

    def test_owner_is_allowed(self):
        self.assertEqual(self.put_product(teams=["owners"]).status_code, 200)

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
            )
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
    def setUp(self):
        auth._teams_cache.clear()

    @mock.patch("webapp.auth.requests.get")
    def test_follows_pagination_and_caches(self, get):
        get.return_value.json.side_effect = [
            {"entries": [{"name": "a"}], "next_collection_link": "next"},
            {"entries": [{"name": "b"}]},
        ]
        self.assertEqual(auth._get_launchpad_teams("user"), ["a", "b"])
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
