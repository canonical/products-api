import unittest

from tests import BaseTestCase
from tests.helpers import _add_product_with_version


class TestGetProductDeployment(BaseTestCase):
    def test_get_product_deployment_returns_200(self):
        """GET /products/<product_slug>/<deployment_slug> returns 200."""
        response = self.client.get("/products/test-product/test-deployment")

        self.assertEqual(response.status_code, 200)

    def test_get_product_deployment_response_shape(self):
        """Response returns a single deployment with nested versions."""
        response = self.client.get("/products/test-product/test-deployment")
        payload = response.get_json()

        self.assertEqual(payload["slug"], "test-deployment")
        self.assertEqual(payload["parent_product"], "test-product")
        self.assertIn("name", payload)
        self.assertIn("artifact_type", payload)
        self.assertIn("versions", payload)
        self.assertIsInstance(payload["versions"], list)
        self.assertGreaterEqual(len(payload["versions"]), 1)

        version = payload["versions"][0]
        self.assertIn("release", version)
        self.assertIn("parent_deployment", version)
        self.assertIn("architecture", version)

    def test_get_product_deployment_excludes_expired_by_default(self):
        """Expired versions are excluded from a deployment by default."""
        _add_product_with_version(
            self.db,
            "deployment-expired-default",
            {
                "supported": {"date": "2000-01-01"},
                "esm_pro_supported": {"date": "2000-01-01"},
                "break_bug_pro_supported": {"date": "2000-01-01"},
                "legacy_supported": {"date": "2000-01-01"},
            },
        )

        response = self.client.get(
            "/products/deployment-expired-default/"
            "deployment-expired-default-deployment"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            payload["slug"], "deployment-expired-default-deployment"
        )
        self.assertEqual(payload["versions"], [])

    def test_get_product_deployment_include_expired_true(self):
        """Expired versions are included with include_expired=true."""
        _add_product_with_version(
            self.db,
            "deployment-expired-true",
            {
                "supported": {"date": "2000-01-01"},
                "esm_pro_supported": {"date": "2000-01-01"},
                "break_bug_pro_supported": {"date": "2000-01-01"},
                "legacy_supported": {"date": "2000-01-01"},
            },
        )

        response = self.client.get(
            "/products/deployment-expired-true/"
            "deployment-expired-true-deployment?include_expired=true"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload["versions"]), 1)

    def test_get_deployment_invalid_include_expired_returns_400(
        self,
    ):
        """Invalid include_expired returns 400 with error fields."""
        response = self.client.get(
            "/products/test-product/test-deployment?include_expired=not-a-bool"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertIn("message", payload["error"])
        self.assertIn("details", payload["error"])
        self.assertIn("include_expired", payload["error"]["details"])

    def test_get_product_deployment_hidden_excluded_by_default(self):
        """Hidden versions are excluded from a deployment by default."""
        _add_product_with_version(
            self.db,
            "deployment-hidden-default",
            {
                "supported": {"date": "2099-01-01"},
                "esm_pro_supported": {"date": "2099-01-01"},
                "break_bug_pro_supported": {"date": "2099-01-01"},
                "legacy_supported": {"date": "2099-01-01"},
            },
            is_hidden=True,
        )

        response = self.client.get(
            "/products/deployment-hidden-default/"
            "deployment-hidden-default-deployment"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            payload["slug"], "deployment-hidden-default-deployment"
        )
        self.assertEqual(payload["versions"], [])

    def test_get_product_deployment_include_hidden_true(self):
        """Hidden versions are included with include_hidden=true."""
        _add_product_with_version(
            self.db,
            "deployment-hidden-true",
            {
                "supported": {"date": "2099-01-01"},
                "esm_pro_supported": {"date": "2099-01-01"},
                "break_bug_pro_supported": {"date": "2099-01-01"},
                "legacy_supported": {"date": "2099-01-01"},
            },
            is_hidden=True,
        )

        response = self.client.get(
            "/products/deployment-hidden-true/"
            "deployment-hidden-true-deployment?include_hidden=true"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload["versions"]), 1)

    def test_get_product_deployment_not_found_returns_404(self):
        """Unknown deployment returns 404 with identifying details."""
        response = self.client.get("/products/test-product/does-not-exist")
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Deployment not found.")
        self.assertEqual(
            payload["error"]["details"],
            {
                "product_slug": "test-product",
                "deployment_slug": "does-not-exist",
            },
        )


if __name__ == "__main__":
    unittest.main()
