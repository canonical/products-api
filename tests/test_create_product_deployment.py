import unittest

from tests import BaseTestCase


class TestCreateProductDeployment(BaseTestCase):
    def test_create_product_deployment_returns_201(self):
        """POST /products/<product_slug> with valid body returns 201."""
        response = self.client.post(
            "/products/test-product",
            json={
                "name": "MicroCeph",
                "artifact_type": "snap",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["slug"], "microceph")
        self.assertEqual(payload["parent_product"], "test-product")
        self.assertEqual(payload["name"], "MicroCeph")
        self.assertEqual(payload["artifact_type"], "snap")
        self.assertEqual(payload["versions"], [])

    def test_create_product_deployment_invalid_body_returns_400(self):
        """Invalid body returns 400 with error message and details."""
        response = self.client.post(
            "/products/test-product",
            json={
                "name": "MicroCeph",
                "artifact_type": "invalid",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")
        self.assertIn("details", payload["error"])
        self.assertIn("artifact_type", payload["error"]["details"])

    def test_create_product_deployment_missing_name_returns_400(self):
        """POST /products/<product_slug> without name returns 400."""
        response = self.client.post(
            "/products/test-product",
            json={
                "artifact_type": "snap",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_deployment_whitespace_only_name_returns_400(self):
        """POST /products/<product_slug> with whitespace name returns 400."""
        response = self.client.post(
            "/products/test-product",
            json={
                "name": "   ",
                "artifact_type": "snap",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_deployment_product_not_found_returns_404(self):
        """Unknown product returns 404 with identifying details."""
        response = self.client.post(
            "/products/does-not-exist",
            json={
                "name": "MicroCeph",
                "artifact_type": "snap",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Product not found.")
        self.assertEqual(
            payload["error"]["details"],
            {"product_slug": "does-not-exist"},
        )

    def test_create_product_deployment_conflict_returns_409(self):
        """Duplicate deployment slug for product returns 409 with details."""
        response = self.client.post(
            "/products/test-product",
            json={
                "name": "Test Deployment",
                "artifact_type": "snap",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 409)
        self.assertIn("error", payload)
        self.assertEqual(
            payload["error"]["message"], "Deployment already exists."
        )
        self.assertEqual(
            payload["error"]["details"],
            {
                "product_slug": "test-product",
                "deployment_slug": "test-deployment",
            },
        )


if __name__ == "__main__":
    unittest.main()
