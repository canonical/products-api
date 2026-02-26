import unittest

from tests import BaseTestCase
from tests.fixtures.models import make_deployment, make_product, make_version


class TestRoutes(BaseTestCase):
    def _add_product_with_version(self, product_slug, lifecycle_overrides):
        product = make_product(
            slug=product_slug,
            name=f"Product {product_slug}",
        )
        deployment = make_deployment(
            product,
            slug=f"{product_slug}-deployment",
            name=f"Deployment {product_slug}",
        )
        version = make_version(
            product,
            deployment,
            release=f"{product_slug}-1.0.0",
            **lifecycle_overrides,
        )
        self.db.session.add(product)
        self.db.session.add(deployment)
        self.db.session.add(version)
        self.db.session.commit()

    def _extract_slugs(self, payload):
        return [product["slug"] for product in payload["products"]]

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
        self._add_product_with_version(
            "expired-default",
            {
                "supported": {"date": "2000-01-01"},
                "pro_supported": {"date": "2000-01-01"},
                "legacy_supported": {"date": "2000-01-01"},
            },
        )

        response = self.client.get("/products")
        payload = response.get_json()
        slugs = self._extract_slugs(payload)

        self.assertNotIn("expired-default", slugs)
        self.assertIn("test-product", slugs)

    def test_get_products_include_expired_true(self):
        """Expired products are included when include_expired=true."""
        self._add_product_with_version(
            "expired-true",
            {
                "supported": {"date": "2000-01-01"},
                "pro_supported": {"date": "2000-01-01"},
                "legacy_supported": {"date": "2000-01-01"},
            },
        )

        response = self.client.get("/products?include_expired=true")
        payload = response.get_json()
        slugs = self._extract_slugs(payload)

        self.assertIn("expired-true", slugs)

    def test_get_products_notes_with_until_not_filtered(self):
        """A version with notes containing 'until' is treated as active and not filtered out."""
        self._add_product_with_version(
            "notes-until",
            {
                "supported": {"notes": "Supported until further notice"},
                "pro_supported": {"notes": "deprecated"},
                "legacy_supported": {"notes": "deprecated"},
            },
        )

        response = self.client.get("/products")
        payload = response.get_json()
        slugs = self._extract_slugs(payload)

        self.assertIn("notes-until", slugs)

    def test_get_products_notes_without_until_filtered(self):
        """A version with notes not containing 'until' and no date is treated as expired."""
        self._add_product_with_version(
            "notes-no-until",
            {
                "supported": {"notes": "deprecated"},
                "pro_supported": {"notes": "deprecated"},
                "legacy_supported": {"notes": "deprecated"},
            },
        )

        response = self.client.get("/products")
        payload = response.get_json()
        slugs = self._extract_slugs(payload)

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