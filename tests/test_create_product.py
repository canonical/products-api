import unittest

from tests import BaseTestCase


class TestCreateProduct(BaseTestCase):
    def test_create_product_returns_201(self):
        """POST /products with valid body returns 201 Created."""
        response = self.client.post(
            "/products",
            json={
                "name": "New Product",
                "deployments": [
                    {
                        "name": "New Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 201)

    def test_create_product_response_shape(self):
        """201 response contains the created product with deployments."""
        response = self.client.post(
            "/products",
            json={
                "name": "Product Shape",
                "deployments": [
                    {
                        "name": "Deployment Shape",
                        "artifact_type": "snap",
                    }
                ],
            },
        )
        payload = response.get_json()

        self.assertEqual(payload["slug"], "product-shape")
        self.assertEqual(payload["name"], "Product Shape")
        self.assertIn("deployments", payload)
        self.assertEqual(len(payload["deployments"]), 1)

        deployment = payload["deployments"][0]
        self.assertEqual(deployment["slug"], "deployment-shape")
        self.assertEqual(deployment["parent_product"], "product-shape")
        self.assertEqual(deployment["name"], "Deployment Shape")
        self.assertEqual(deployment["artifact_type"], "snap")
        self.assertEqual(deployment["versions"], [])

    def test_create_product_missing_deployments_returns_400(self):
        """POST /products without deployments returns 400."""
        response = self.client.post(
            "/products",
            json={
                "name": "No Deployments",
                "deployments": [],
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_invalid_artifact_type_returns_400(self):
        """POST /products with invalid artifact_type returns 400."""
        response = self.client.post(
            "/products",
            json={
                "name": "Invalid Type",
                "deployments": [
                    {
                        "name": "Invalid Dep",
                        "artifact_type": "invalid",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("error", payload)

    def test_create_product_duplicate_slug_returns_409(self):
        """POST /products with a name that generates an existing slug returns 409."""
        response = self.client.post(
            "/products",
            json={
                "name": "Test Product",
                "deployments": [
                    {
                        "name": "New Dep",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertIn("error", payload)
        self.assertEqual(
            payload["error"]["message"],
            "Product or deployment slug already exists.",
        )
        self.assertEqual(
            payload["error"]["details"],
            {"product_slug": "test-product"},
        )

    def test_create_product_missing_name_returns_400(self):
        """POST /products without name returns 400 with error.details."""
        response = self.client.post(
            "/products",
            json={
                "deployments": [
                    {
                        "name": "No Name Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_whitespace_only_name_returns_400(self):
        """POST /products with a whitespace-only name returns 400 with error.details."""
        response = self.client.post(
            "/products",
            json={
                "name": "   ",
                "deployments": [
                    {
                        "name": "Blank Name Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_preserves_name_casing(self):
        """POST /products preserves name casing exactly as provided."""
        response = self.client.post(
            "/products",
            json={
                "name": "etcd",
                "deployments": [
                    {
                        "name": "Etcd Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["name"], "etcd")

    def test_create_product_missing_deployments_key_returns_400(self):
        """POST /products with deployments key omitted entirely returns 400 with error.details."""
        response = self.client.post(
            "/products",
            json={
                "name": "No Deployments Key",
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_slug_autogenerated_from_name(self):
        """POST /products generates the expected slug from the product name."""
        response = self.client.post(
            "/products",
            json={
                "name": "Charmed Ceph",
                "deployments": [
                    {
                        "name": "Charmed Ceph Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["slug"], "charmed-ceph")

    def test_create_product_duplicate_deployment_names_returns_400(self):
        """POST /products with duplicate deployment names returns 400 with error.details."""
        response = self.client.post(
            "/products",
            json={
                "name": "Duplicate Dep Names Product",
                "deployments": [
                    {
                        "name": "My Deployment",
                        "artifact_type": "charm",
                    },
                    {
                        "name": "my deployment",
                        "artifact_type": "snap",
                    },
                ],
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])


if __name__ == "__main__":
    unittest.main()
