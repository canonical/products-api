from webapp.models import Deployment, Product, Version


def make_product(**overrides):
    """Create a Product instance with sensible defaults."""
    defaults = {
        "slug": "test-product",
        "name": "Test Product",
    }
    return Product(**{**defaults, **overrides})


def make_deployment(product, **overrides):
    """Create a Deployment instance attached to a product."""
    defaults = {
        "slug": "test-deployment",
        "parent_product": product.slug,
        "name": "Test Deployment",
        "artifact_type": "snap",
    }
    return Deployment(**{**defaults, **overrides})


def make_version(product, deployment, **overrides):
    """Create a Version with required DateOrNote fields.

    Uses future-default lifecycle dates unless overridden.
    """
    future_date = {"date": "2099-01-01"}
    defaults = {
        "parent_product": product.slug,
        "parent_deployment": deployment.slug,
        "release": "1.0.0",
        "architecture": ["amd64"],
        "release_date": {"date": "2020-01-01"},
        "supported": future_date,
        "esm_pro_supported": future_date,
        "break_bug_pro_supported": future_date,
        "legacy_supported": future_date,
        "upgrade_path": None,
        "compatible_ubuntu_lts": None,
        "is_hidden": False,
    }
    return Version(**{**defaults, **overrides})


def make_models():
    """Return a dict with a fully linked product, deployment and version."""
    product = make_product()
    deployment = make_deployment(product)
    version = make_version(product, deployment)
    return {
        "product": product,
        "deployment": deployment,
        "version": version,
    }
