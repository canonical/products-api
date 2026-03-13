import unittest

from tests import BaseTestCase
from tests.helpers import _add_product_with_version, _extract_slugs


class TestRoutes(BaseTestCase):
    def test_get_products_returns_200(self):
        """GET /products returns 200."""
        response = self.client.get("/products")

        self.assertEqual(response.status_code, 200)

    def test_get_products_response_shape(self):
        """Response contains a products key with nested deployments and versions."""
        response = self.client.get("/products")
        payload = response.get_json()

        self.assertIn("products", payload)
        self.assertIsInstance(payload["products"], list)
        self.assertGreaterEqual(len(payload["products"]), 1)

        product = payload["products"][0]
        self.assertIn("deployments", product)
        self.assertIsInstance(product["deployments"], list)
        self.assertGreaterEqual(len(product["deployments"]), 1)

        deployment = product["deployments"][0]
        self.assertIn("versions", deployment)
        self.assertIsInstance(deployment["versions"], list)
        self.assertGreaterEqual(len(deployment["versions"]), 1)

    def test_get_products_excludes_expired_by_default(self):
        """Products where all versions are expired are excluded when include_expired is omitted."""
        _add_product_with_version(
            self.db,
            "expired-default",
            {
                "supported": {"date": "2000-01-01"},
                "pro_supported": {"date": "2000-01-01"},
                "legacy_supported": {"date": "2000-01-01"},
            },
        )

        response = self.client.get("/products")
        payload = response.get_json()
        slugs = _extract_slugs(payload)

        self.assertNotIn("expired-default", slugs)
        self.assertIn("test-product", slugs)

    def test_get_products_include_expired_true(self):
        """Expired products are included when include_expired=true."""
        _add_product_with_version(
            self.db,
            "expired-true",
            {
                "supported": {"date": "2000-01-01"},
                "pro_supported": {"date": "2000-01-01"},
                "legacy_supported": {"date": "2000-01-01"},
            },
        )

        response = self.client.get("/products?include_expired=true")
        payload = response.get_json()
        slugs = _extract_slugs(payload)

        self.assertIn("expired-true", slugs)

    def test_get_products_notes_with_until_not_filtered(self):
        """A version with notes containing 'until' is treated as active and not filtered out."""
        _add_product_with_version(
            self.db,
            "notes-until",
            {
                "supported": {"notes": "Supported until further notice"},
                "pro_supported": {"notes": "deprecated"},
                "legacy_supported": {"notes": "deprecated"},
            },
        )

        response = self.client.get("/products")
        payload = response.get_json()
        slugs = _extract_slugs(payload)

        self.assertIn("notes-until", slugs)

    def test_get_products_notes_without_until_filtered(self):
        """A version with notes not containing 'until' and no date is treated as expired."""
        _add_product_with_version(
            self.db,
            "notes-no-until",
            {
                "supported": {"notes": "deprecated"},
                "pro_supported": {"notes": "deprecated"},
                "legacy_supported": {"notes": "deprecated"},
            },
        )

        response = self.client.get("/products")
        payload = response.get_json()
        slugs = _extract_slugs(payload)

        self.assertNotIn("notes-no-until", slugs)

    def test_get_products_invalid_include_expired_returns_400(self):
        """An invalid include_expired value returns 400 with the correct error shape."""
        response = self.client.get("/products?include_expired=not-a-bool")

        self.assertEqual(response.status_code, 400)

    def test_get_products_invalid_include_expired_error_shape(self):
        """400 response contains error.message and error.details keys."""
        response = self.client.get("/products?include_expired=not-a-bool")
        payload = response.get_json()

        self.assertIn("error", payload)
        self.assertIn("message", payload["error"])
        self.assertIn("details", payload["error"])
        self.assertIn("include_expired", payload["error"]["details"])


if __name__ == "__main__":
    unittest.main()