import unittest

from tests import BaseTestCase


class TestCreateProduct(BaseTestCase):
    def test_create_product_returns_201(self):
        """POST /products with valid body returns 201 Created."""
        response = self.client.post(
            "/products",
            json={
                "slug": "new-product",
                "name": "New Product",
                "deployments": [
                    {
                        "slug": "new-deployment",
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
                "slug": "product-shape",
                "name": "Product Shape",
                "deployments": [
                    {
                        "slug": "deployment-shape",
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
                "slug": "no-deployments",
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
                "slug": "invalid-type",
                "name": "Invalid Type",
                "deployments": [
                    {
                        "slug": "invalid-dep",
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
        """POST /products with existing product slug returns 409."""
        response = self.client.post(
            "/products",
            json={
                "slug": "test-product",
                "name": "Test Product",
                "deployments": [
                    {
                        "slug": "new-dep",
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

    def test_create_product_duplicate_deployment_slugs_in_request_returns_400(self):
        """POST /products with duplicate deployment slugs in request returns 400."""
        response = self.client.post(
            "/products",
            json={
                "slug": "request-dup-product",
                "name": "Request Duplicate Product",
                "deployments": [
                    {
                        "slug": "duplicate-deployment",
                        "name": "Deployment One",
                        "artifact_type": "charm",
                    },
                    {
                        "slug": "duplicate-deployment",
                        "name": "Deployment Two",
                        "artifact_type": "snap",
                    },
                ],
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_without_slug_autogenerates_slug(self):
        """Omitting slug generates a non-empty slug from the product name."""
        response = self.client.post(
            "/products",
            json={
                "name": "Auto Generated Slug",
                "deployments": [
                    {
                        "slug": "auto-gen-dep",
                        "name": "Auto Gen Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertIsInstance(payload["slug"], str)
        self.assertGreater(len(payload["slug"]), 0)

    def test_create_product_whitespace_slug_autogenerates_slug(self):
        """POST /products with a whitespace-only slug auto-generates a non-empty slug."""
        response = self.client.post(
            "/products",
            json={
                "slug": "   ",
                "name": "Whitespace Slug",
                "deployments": [
                    {
                        "slug": "ws-dep",
                        "name": "Ws Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertIsInstance(payload["slug"], str)
        self.assertGreater(len(payload["slug"]), 0)

    def test_create_product_invalid_slug_format_returns_400(self):
        """POST /products with a slug that does not match the allowed pattern returns 400."""
        response = self.client.post(
            "/products",
            json={
                "slug": "Invalid Slug!",
                "name": "Invalid Slug",
                "deployments": [
                    {
                        "slug": "inv-dep",
                        "name": "Inv Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_create_product_missing_name_returns_400(self):
        """POST /products without name returns 400 with error.details."""
        response = self.client.post(
            "/products",
            json={
                "slug": "no-name-product",
                "deployments": [
                    {
                        "slug": "no-name-dep",
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
                "slug": "blank-name-product",
                "name": "   ",
                "deployments": [
                    {
                        "slug": "blank-name-dep",
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
                "slug": "etcd-product",
                "name": "etcd",
                "deployments": [
                    {
                        "slug": "etcd-dep",
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
                "slug": "no-deps-key",
                "name": "No Deployments Key",
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_deployment_without_slug_autogenerates_slug(self):
        """Omitting slug in a deployment auto-generates a non-empty slug."""
        response = self.client.post(
            "/products",
            json={
                "slug": "dep-autogen-product",
                "name": "Deployment Autogen Product",
                "deployments": [
                    {
                        "name": "Auto Generated Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(len(payload["deployments"]), 1)
        deployment = payload["deployments"][0]
        self.assertIsInstance(deployment["slug"], str)
        self.assertGreater(len(deployment["slug"]), 0)

    def test_create_product_deployment_whitespace_slug_autogenerates_slug(self):
        """Providing a whitespace-only slug in a deployment auto-generates a non-empty slug."""
        response = self.client.post(
            "/products",
            json={
                "slug": "dep-ws-product",
                "name": "Deployment Whitespace Product",
                "deployments": [
                    {
                        "slug": "   ",
                        "name": "Whitespace Deployment",
                        "artifact_type": "charm",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(len(payload["deployments"]), 1)
        deployment = payload["deployments"][0]
        self.assertIsInstance(deployment["slug"], str)
        self.assertGreater(len(deployment["slug"]), 0)


if __name__ == "__main__":
    unittest.main()
