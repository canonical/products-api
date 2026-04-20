import unittest

from tests import BaseTestCase


class TestGetProductDeploymentVersion(BaseTestCase):
    def test_get_product_deployment_version_returns_200(self):
        """GET /products/<product_slug>/<deployment_slug>/<release> returns 200."""
        response = self.client.get(
            "/products/test-product/test-deployment/1.0.0"
        )

        self.assertEqual(response.status_code, 200)

    def test_get_product_deployment_version_response_shape(self):
        """Response returns version details using current VersionSchema fields."""
        response = self.client.get(
            "/products/test-product/test-deployment/1.0.0"
        )
        payload = response.get_json()

        self.assertEqual(payload["parent_product"], "test-product")
        self.assertEqual(payload["parent_deployment"], "test-deployment")
        self.assertEqual(payload["release"], "1.0.0")
        self.assertIn("architecture", payload)
        self.assertIn("release_date", payload)
        self.assertIn("supported", payload)
        self.assertIn("esm_pro_supported", payload)
        self.assertIn("break_bug_pro_supported", payload)
        self.assertIn("legacy_supported", payload)

    def test_get_product_deployment_version_not_found_returns_404(self):
        """Unknown version returns 404 with identifying details."""
        response = self.client.get(
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


if __name__ == "__main__":
    unittest.main()
