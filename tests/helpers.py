from tests.fixtures.models import make_deployment, make_product, make_version


def _add_product_with_version(
    db, product_slug, lifecycle_overrides, is_hidden=False
):
    product = make_product(
        slug=product_slug,
        name=f"Product {product_slug}",
    )
    deployment = make_deployment(
        product,
        slug=f"{product_slug}-deployment",
        name=f"Deployment {product_slug}",
    )
    version = make_version(
        product,
        deployment,
        release=f"{product_slug}-1.0.0",
        is_hidden=is_hidden,
        **lifecycle_overrides,
    )
    db.session.add(product)
    db.session.add(deployment)
    db.session.add(version)
    db.session.commit()


def _extract_slugs(payload):
    return [product["slug"] for product in payload["products"]]
