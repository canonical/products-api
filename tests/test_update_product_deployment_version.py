import unittest

from tests import BaseTestCase


class TestUpdateProductDeploymentVersion(BaseTestCase):
    def test_update_product_deployment_version_updates_fields_and_returns_200(self):
        """PUT updates version fields and returns 200 with updated payload."""
        response = self.client.put(
            "/products/test-product/test-deployment/1.0.0",
            json={
                "architecture": ["amd64", "arm64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2099-01-01"},
                "esm_pro_supported": {"date": "2099-01-01"},
                "break_bug_pro_supported": {"date": "2099-01-01"},
                "legacy_supported": {"notes": "until further notice"},
                "upgrade_path": ["0.9.0"],
                "compatible_ubuntu_lts": [
                    {
                        "version": "22.04",
                        "compatible_components": ["component-a"],
                    }
                ],
                "is_hidden": True,
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["parent_product"], "test-product")
        self.assertEqual(payload["parent_deployment"], "test-deployment")
        self.assertEqual(payload["release"], "1.0.0")
        self.assertEqual(payload["architecture"], ["amd64", "arm64"])
        self.assertEqual(payload["release_date"], {"date": "2026-01-01"})
        self.assertEqual(payload["supported"], {"date": "2099-01-01"})
        self.assertEqual(payload["esm_pro_supported"], {"date": "2099-01-01"})
        self.assertEqual(
            payload["break_bug_pro_supported"], {"date": "2099-01-01"}
        )
        self.assertEqual(
            payload["legacy_supported"], {"notes": "until further notice"}
        )
        self.assertEqual(payload["upgrade_path"], ["0.9.0"])
        self.assertEqual(
            payload["compatible_ubuntu_lts"],
            [
                {
                    "version": "22.04",
                    "compatible_components": ["component-a"],
                }
            ],
        )
        self.assertEqual(payload["is_hidden"], True)

    def test_update_product_deployment_version_single_field_updates(self):
        """PUT can update a single field without requiring other fields."""
        response = self.client.put(
            "/products/test-product/test-deployment/1.0.0",
            json={"is_hidden": True},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["release"], "1.0.0")
        self.assertEqual(payload["is_hidden"], True)

    def test_update_product_deployment_version_empty_body_returns_400(self):
        """PUT with empty body returns 400 with existing error shape."""
        response = self.client.put(
            "/products/test-product/test-deployment/1.0.0",
            json={},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")
        self.assertIn("details", payload["error"])

    def test_update_product_deployment_version_invalid_architecture_returns_400(self):
        """PUT with invalid architecture returns 400 with field details."""
        response = self.client.put(
            "/products/test-product/test-deployment/1.0.0",
            json={"architecture": ["invalid-arch"]},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")
        self.assertIn("details", payload["error"])
        self.assertIn("architecture", payload["error"]["details"])

    def test_update_product_deployment_version_not_found_returns_404(self):
        """Unknown version returns 404 with identifying details."""
        response = self.client.put(
            "/products/test-product/test-deployment/does-not-exist",
            json={"is_hidden": True},
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

    def test_update_product_deployment_version_deployment_not_found_returns_404(self):
        """Unknown deployment returns 404 with identifying details."""
        response = self.client.put(
            "/products/test-product/does-not-exist/1.0.0",
            json={"is_hidden": True},
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

    def test_update_product_deployment_version_product_not_found_returns_404(self):
        """Unknown product returns 404 with identifying details."""
        response = self.client.put(
            "/products/does-not-exist/test-deployment/1.0.0",
            json={"is_hidden": True},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Product not found.")
        self.assertEqual(
            payload["error"]["details"],
            {"product_slug": "does-not-exist"},
        )

    def test_update_version_lifecycle_date_before_release_date_returns_400(self):
        """PUT with a lifecycle date before the stored release_date returns 400."""
        response = self.client.put(
            "/products/test-product/test-deployment/1.0.0",
            json={
                "supported": {"date": "2019-01-01"},
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")
        self.assertIn("supported", payload["error"]["details"])

    def test_update_version_new_release_date_before_existing_lifecycle_returns_400(
        self,
    ):
        """PUT with a release_date after existing lifecycle dates returns 400."""
        response = self.client.put(
            "/products/test-product/test-deployment/1.0.0",
            json={
                "release_date": {"date": "2100-01-01"},
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")

    def test_update_version_notes_only_lifecycle_not_checked_against_release_date(
        self,
    ):
        """PUT with notes-only lifecycle fields is not subject to date ordering validation."""
        response = self.client.put(
            "/products/test-product/test-deployment/1.0.0",
            json={
                "supported": {"notes": "until further notice"},
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)

    def test_update_version_release_date_and_lifecycle_date_same_day_is_valid(
        self,
    ):
        """PUT with a lifecycle date equal to release_date is valid."""
        response = self.client.put(
            "/products/test-product/test-deployment/1.0.0",
            json={
                "supported": {"date": "2020-01-01"},
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
