import unittest

from tests import BaseTestCase


class TestUpdateProductDeployment(BaseTestCase):
    def test_update_product_deployment_updates_both_fields_and_returns_200(
        self,
    ):
        """PUT updates deployment name/artifact_type and keeps slug."""
        response = self.client.put(
            "/products/test-product/test-deployment",
            json={
                "name": "Canonical Charmed Ceph Updated",
                "artifact_type": "charm",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["slug"], "test-deployment")
        self.assertEqual(payload["parent_product"], "test-product")
        self.assertEqual(payload["name"], "Canonical Charmed Ceph Updated")
        self.assertEqual(payload["artifact_type"], "charm")
        self.assertIn("versions", payload)

    def test_update_product_deployment_updates_name_only(self):
        """PUT updates only name when artifact_type is omitted."""
        response = self.client.put(
            "/products/test-product/test-deployment",
            json={"name": "Updated Deployment Name"},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["slug"], "test-deployment")
        self.assertEqual(payload["name"], "Updated Deployment Name")
        self.assertEqual(payload["artifact_type"], "snap")

    def test_update_product_deployment_updates_artifact_type_only(self):
        """PUT updates only artifact_type when name is omitted."""
        response = self.client.put(
            "/products/test-product/test-deployment",
            json={"artifact_type": "rock"},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["slug"], "test-deployment")
        self.assertEqual(payload["name"], "Test Deployment")
        self.assertEqual(payload["artifact_type"], "rock")

    def test_update_product_deployment_empty_body_returns_400(self):
        """PUT with empty body returns 400 using existing error shape."""
        response = self.client.put(
            "/products/test-product/test-deployment",
            json={},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")
        self.assertIn("details", payload["error"])

    def test_update_product_deployment_invalid_artifact_type_returns_400(self):
        """PUT with invalid artifact_type returns 400 with field details."""
        response = self.client.put(
            "/products/test-product/test-deployment",
            json={"artifact_type": "invalid"},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")
        self.assertIn("details", payload["error"])
        self.assertIn("artifact_type", payload["error"]["details"])

    def test_update_product_deployment_whitespace_name_returns_400(self):
        """PUT with whitespace-only name returns 400 with name details."""
        response = self.client.put(
            "/products/test-product/test-deployment",
            json={"name": "   "},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")
        self.assertIn("details", payload["error"])
        self.assertIn("name", payload["error"]["details"])

    def test_update_product_deployment_not_found_returns_404(self):
        """PUT unknown deployment returns 404 with identifying details."""
        response = self.client.put(
            "/products/test-product/does-not-exist",
            json={"name": "Updated Deployment Name"},
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

    def test_update_product_deployment_product_not_found_returns_404(self):
        """Unknown product returns 404 with identifying details."""
        response = self.client.put(
            "/products/does-not-exist/test-deployment",
            json={
                "name": "Updated Deployment Name",
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


if __name__ == "__main__":
    unittest.main()
