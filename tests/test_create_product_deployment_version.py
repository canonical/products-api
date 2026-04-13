import unittest

from tests import BaseTestCase


class TestCreateProductDeploymentVersion(BaseTestCase):
    def test_create_product_deployment_version_returns_201(self):
        """POST /products/<product_slug>/<deployment_slug> with valid body returns 201."""
        response = self.client.post(
            "/products/test-product/test-deployment",
            json={
                "release": "2.0.0",
                "architecture": ["amd64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2026-12-31"},
                "esm_pro_supported": {"date": "2027-12-31"},
                "break_bug_pro_supported": {"date": "2028-12-31"},
                "legacy_supported": {"notes": "until further notice"},
                "upgrade_path": ["1.0.0"],
                "compatible_ubuntu_lts": [
                    {
                        "version": "22.04",
                        "compatible_components": ["component-a"],
                    }
                ],
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["parent_product"], "test-product")
        self.assertEqual(payload["parent_deployment"], "test-deployment")
        self.assertEqual(payload["release"], "2.0.0")
        self.assertEqual(payload["architecture"], ["amd64"])
        self.assertEqual(payload["is_hidden"], False)

    def test_create_product_deployment_version_hidden_excluded_by_default(self):
        """A version created with is_hidden=True is excluded from GET by default."""
        self.client.post(
            "/products/test-product/test-deployment",
            json={
                "release": "hidden-1.0.0",
                "architecture": ["amd64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2099-01-01"},
                "esm_pro_supported": {"date": "2099-01-01"},
                "break_bug_pro_supported": {"date": "2099-01-01"},
                "legacy_supported": {"notes": "until further notice"},
                "is_hidden": True,
            },
        )

        response = self.client.get("/products/test-product/test-deployment")
        payload = response.get_json()

        releases = [v["release"] for v in payload["versions"]]
        self.assertNotIn("hidden-1.0.0", releases)

    def test_create_product_deployment_version_hidden_included_with_param(self):
        """A version created with is_hidden=True is included when include_hidden=true."""
        self.client.post(
            "/products/test-product/test-deployment",
            json={
                "release": "hidden-2.0.0",
                "architecture": ["amd64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2099-01-01"},
                "esm_pro_supported": {"date": "2099-01-01"},
                "break_bug_pro_supported": {"date": "2099-01-01"},
                "legacy_supported": {"notes": "until further notice"},
                "is_hidden": True,
            },
        )

        response = self.client.get(
            "/products/test-product/test-deployment?include_hidden=true"
        )
        payload = response.get_json()

        releases = [v["release"] for v in payload["versions"]]
        self.assertIn("hidden-2.0.0", releases)

    def test_create_product_deployment_version_invalid_body_returns_400(self):
        """Invalid request body returns 400 with error details."""
        response = self.client.post(
            "/products/test-product/test-deployment",
            json={
                "release": "2.0.2",
                "architecture": ["invalid-arch"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2026-12-31"},
                "esm_pro_supported": {"date": "2027-12-31"},
                "break_bug_pro_supported": {"date": "2028-12-31"},
                "legacy_supported": {"notes": "until further notice"},
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Invalid request.")
        self.assertIn("details", payload["error"])

    def test_create_product_deployment_version_missing_release_returns_400(self):
        """POST without release returns 400 with error.details."""
        response = self.client.post(
            "/products/test-product/test-deployment",
            json={
                "architecture": ["amd64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2026-12-31"},
                "esm_pro_supported": {"date": "2027-12-31"},
                "break_bug_pro_supported": {"date": "2028-12-31"},
                "legacy_supported": {"notes": "until further notice"},
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_deployment_version_whitespace_only_release_returns_400(self):
        """POST with whitespace-only release returns 400 with error.details."""
        response = self.client.post(
            "/products/test-product/test-deployment",
            json={
                "release": "   ",
                "architecture": ["amd64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2026-12-31"},
                "esm_pro_supported": {"date": "2027-12-31"},
                "break_bug_pro_supported": {"date": "2028-12-31"},
                "legacy_supported": {"notes": "until further notice"},
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_deployment_version_missing_required_field_returns_400(self):
        """POST without a required lifecycle field returns 400 with error.details."""
        response = self.client.post(
            "/products/test-product/test-deployment",
            json={
                "release": "3.0.0",
                "architecture": ["amd64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2026-12-31"},
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", payload)
        self.assertIn("details", payload["error"])

    def test_create_product_deployment_version_product_not_found_returns_404(self):
        """Unknown product returns 404 with identifying details."""
        response = self.client.post(
            "/products/does-not-exist/test-deployment",
            json={
                "release": "2.0.3",
                "architecture": ["amd64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2026-12-31"},
                "esm_pro_supported": {"date": "2027-12-31"},
                "break_bug_pro_supported": {"date": "2028-12-31"},
                "legacy_supported": {"notes": "until further notice"},
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

    def test_create_product_deployment_version_deployment_not_found_returns_404(self):
        """Unknown deployment returns 404 with identifying details."""
        response = self.client.post(
            "/products/test-product/does-not-exist",
            json={
                "release": "2.0.4",
                "architecture": ["amd64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2026-12-31"},
                "esm_pro_supported": {"date": "2027-12-31"},
                "break_bug_pro_supported": {"date": "2028-12-31"},
                "legacy_supported": {"notes": "until further notice"},
            },
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

    def test_create_product_deployment_version_conflict_returns_409(self):
        """Duplicate release for deployment returns 409 with details."""
        response = self.client.post(
            "/products/test-product/test-deployment",
            json={
                "release": "1.0.0",
                "architecture": ["amd64"],
                "release_date": {"date": "2026-01-01"},
                "supported": {"date": "2026-12-31"},
                "esm_pro_supported": {"date": "2027-12-31"},
                "break_bug_pro_supported": {"date": "2028-12-31"},
                "legacy_supported": {"notes": "until further notice"},
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 409)
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["message"], "Version already exists.")
        self.assertEqual(
            payload["error"]["details"],
            {
                "product_slug": "test-product",
                "deployment_slug": "test-deployment",
                "release": "1.0.0",
            },
        )


if __name__ == "__main__":
    unittest.main()
