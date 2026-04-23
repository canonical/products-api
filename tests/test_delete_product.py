import unittest

from tests import BaseTestCase
from webapp.models import Deployment, Product, Version


class TestDeleteProduct(BaseTestCase):
    def test_delete_product_returns_200_with_deleted_payload(self):
        """DELETE /products/<product_slug> returns deleted product metadata."""
        response = self.client.delete("/products/test-product")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            payload,
            {
                "deleted": {
                    "slug": "test-product",
                    "name": "Test Product",
                }
            },
        )

    def test_delete_product_not_found_returns_404(self):
        """Unknown product slug returns 404 with product_slug detail."""
        response = self.client.delete("/products/does-not-exist")
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Product not found.")
        self.assertEqual(
            payload["error"]["details"],
            {"product_slug": "does-not-exist"},
        )

    def test_delete_product_cascades_to_deployments_and_versions(self):
        """Deleting a product cascades to related deployments and versions."""
        response = self.client.delete("/products/test-product")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(
            Product.query.filter_by(slug="test-product").one_or_none()
        )
        self.assertIsNone(
            Deployment.query.filter_by(
                parent_product="test-product",
                slug="test-deployment",
            ).one_or_none()
        )
        self.assertIsNone(
            Version.query.filter_by(
                parent_product="test-product",
                parent_deployment="test-deployment",
                release="1.0.0",
            ).one_or_none()
        )


if __name__ == "__main__":
    unittest.main()
