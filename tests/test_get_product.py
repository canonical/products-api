import unittest

from tests import BaseTestCase
from tests.helpers import _add_product_with_version


class TestGetProduct(BaseTestCase):
    def test_get_product_returns_200(self):
        """GET /products/<product_slug> returns 200 for existing product."""
        response = self.client.get("/products/test-product")

        self.assertEqual(response.status_code, 200)

    def test_get_product_response_shape(self):
        """Response returns a single product with nested deployments and versions."""
        response = self.client.get("/products/test-product")
        payload = response.get_json()

        self.assertIn("slug", payload)
        self.assertEqual(payload["slug"], "test-product")
        self.assertIn("name", payload)
        self.assertIn("deployments", payload)
        self.assertIsInstance(payload["deployments"], list)
        self.assertGreaterEqual(len(payload["deployments"]), 1)

        deployment = payload["deployments"][0]
        self.assertIn("versions", deployment)
        self.assertIsInstance(deployment["versions"], list)
        self.assertGreaterEqual(len(deployment["versions"]), 1)

    def test_get_product_excludes_expired_by_default(self):
        """Expired versions are excluded when include_expired is omitted."""
        _add_product_with_version(
            self.db,
            "single-expired-default",
            {
                "supported": {"date": "2000-01-01"},
                "pro_supported": {"date": "2000-01-01"},
                "legacy_supported": {"date": "2000-01-01"},
            },
        )

        response = self.client.get("/products/single-expired-default")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["slug"], "single-expired-default")
        self.assertEqual(payload["deployments"], [])

    def test_get_product_include_expired_true(self):
        """Expired versions are included when include_expired=true."""
        _add_product_with_version(
            self.db,
            "single-expired-true",
            {
                "supported": {"date": "2000-01-01"},
                "pro_supported": {"date": "2000-01-01"},
                "legacy_supported": {"date": "2000-01-01"},
            },
        )

        response = self.client.get(
            "/products/single-expired-true?include_expired=true"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload["deployments"]), 1)
        self.assertEqual(len(payload["deployments"][0]["versions"]), 1)

    def test_get_product_invalid_include_expired_returns_400_with_error_shape(self):
        """Invalid include_expired returns 400 with error.message and error.details."""
        response = self.client.get(
            "/products/test-product?include_expired=not-a-bool"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertIn("message", payload["error"])
        self.assertIn("details", payload["error"])
        self.assertIn("include_expired", payload["error"]["details"])

    def test_get_product_not_found_returns_404(self):
        """Unknown product slug returns 404 with product_slug detail."""
        response = self.client.get("/products/does-not-exist")
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Product not found.")
        self.assertEqual(
            payload["error"]["details"],
            {"product_slug": "does-not-exist"},
        )


if __name__ == "__main__":
    unittest.main()
