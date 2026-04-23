import unittest

from tests import BaseTestCase
from webapp.models import Version


class TestDeleteProductDeploymentVersion(BaseTestCase):
    def test_delete_version_returns_200_with_deleted_payload(
        self,
    ):
        """DELETE returns deleted version metadata."""
        response = self.client.delete(
            "/products/test-product/test-deployment/1.0.0"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            payload,
            {
                "deleted": {
                    "release": "1.0.0",
                    "parent_deployment": "test-deployment",
                    "parent_product": "test-product",
                }
            },
        )

    def test_delete_product_deployment_version_product_not_found_returns_404(
        self,
    ):
        """Unknown product returns 404 with identifying details."""
        response = self.client.delete(
            "/products/does-not-exist/test-deployment/1.0.0"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Product not found.")
        self.assertEqual(
            payload["error"]["details"],
            {"product_slug": "does-not-exist"},
        )

    def test_delete_version_deployment_not_found_returns_404(
        self,
    ):
        """Unknown deployment returns 404 with identifying details."""
        response = self.client.delete(
            "/products/test-product/does-not-exist/1.0.0"
        )
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

    def test_delete_product_deployment_version_not_found_returns_404(self):
        """Unknown version returns 404 with identifying details."""
        response = self.client.delete(
            "/products/test-product/test-deployment/does-not-exist"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Version not found.")
        self.assertEqual(
            payload["error"]["details"],
            {
                "product_slug": "test-product",
                "deployment_slug": "test-deployment",
                "release": "does-not-exist",
            },
        )

    def test_delete_product_deployment_version_removes_version(self):
        """Deleting a version removes only that version record."""
        response = self.client.delete(
            "/products/test-product/test-deployment/1.0.0"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(
            Version.query.filter_by(
                parent_product="test-product",
                parent_deployment="test-deployment",
                release="1.0.0",
            ).one_or_none()
        )


if __name__ == "__main__":
    unittest.main()
