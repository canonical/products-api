import unittest

from tests import BaseTestCase
from tests.fixtures.models import make_deployment, make_version
from webapp.models import Deployment, Product, Version


class TestDeleteProductDeployment(BaseTestCase):
    def test_delete_product_deployment_returns_200_with_deleted_payload(self):
        """DELETE returns deleted deployment metadata."""
        product = self.models["product"]
        second_deployment = make_deployment(
            product,
            slug="second-deployment",
            name="Second Deployment",
        )
        second_version = make_version(
            product,
            second_deployment,
            release="2.0.0",
        )
        self.db.session.add(second_deployment)
        self.db.session.add(second_version)
        self.db.session.commit()

        response = self.client.delete(
            "/products/test-product/second-deployment"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            payload,
            {
                "deleted": {
                    "slug": "second-deployment",
                    "parent_product": "test-product",
                }
            },
        )

    def test_delete_product_deployment_product_not_found_returns_404(self):
        """Unknown product returns 404 with identifying details."""
        response = self.client.delete(
            "/products/does-not-exist/test-deployment"
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Product not found.")
        self.assertEqual(
            payload["error"]["details"],
            {"product_slug": "does-not-exist"},
        )

    def test_delete_product_deployment_not_found_returns_404(self):
        """Unknown deployment returns 404 with identifying details."""
        response = self.client.delete("/products/test-product/does-not-exist")
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

    def test_delete_product_deployment_last_remaining_returns_400(self):
        """Deleting the last deployment returns 400 and does not delete it."""
        response = self.client.delete("/products/test-product/test-deployment")
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(
            payload["error"]["message"],
            "Cannot delete the last deployment.",
        )
        self.assertEqual(
            payload["error"]["details"],
            {"reason": ("Products must have at least one deployment.")},
        )
        self.assertIsNotNone(
            Deployment.query.filter_by(
                parent_product="test-product",
                slug="test-deployment",
            ).one_or_none()
        )

    def test_delete_product_deployment_cascades_versions_for_deleted(
        self,
    ):
        """
        Deleting one deployment removes its versions and keeps the product
        and other deployment.
        """
        product = self.models["product"]
        second_deployment = make_deployment(
            product,
            slug="second-deployment",
            name="Second Deployment",
        )
        second_version = make_version(
            product,
            second_deployment,
            release="2.0.0",
        )
        self.db.session.add(second_deployment)
        self.db.session.add(second_version)
        self.db.session.commit()

        response = self.client.delete(
            "/products/test-product/second-deployment"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(
            Deployment.query.filter_by(
                parent_product="test-product",
                slug="second-deployment",
            ).one_or_none()
        )
        self.assertIsNone(
            Version.query.filter_by(
                parent_product="test-product",
                parent_deployment="second-deployment",
                release="2.0.0",
            ).one_or_none()
        )
        self.assertIsNotNone(
            Product.query.filter_by(slug="test-product").one_or_none()
        )
        self.assertIsNotNone(
            Deployment.query.filter_by(
                parent_product="test-product",
                slug="test-deployment",
            ).one_or_none()
        )


if __name__ == "__main__":
    unittest.main()
