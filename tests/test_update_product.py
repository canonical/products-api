import unittest

from tests import BaseTestCase


class TestPutProduct(BaseTestCase):
    def test_put_product_updates_name_and_returns_200(self):
        """PUT /products/<product_slug> updates product name and is 200."""
        response = self.client.put(
            "/products/test-product",
            json={"name": "Updated Product Name"},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["slug"], "test-product")
        self.assertEqual(payload["name"], "Updated Product Name")
        self.assertIn("deployments", payload)

    def test_put_product_invalid_body_returns_400(self):
        """Missing name in body returns 400 with existing error shape."""
        response = self.client.put(
            "/products/test-product",
            json={},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")
        self.assertIn("details", payload["error"])
        self.assertIn("name", payload["error"]["details"])

    def test_put_product_whitespace_only_name_returns_400(self):
        """PUT with whitespace-only product name returns 400."""
        response = self.client.put(
            "/products/test-product",
            json={"name": "   "},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_put_product_not_found_returns_404(self):
        """Unknown product slug returns 404 with product_slug detail."""
        response = self.client.put(
            "/products/does-not-exist",
            json={"name": "Updated Product Name"},
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
