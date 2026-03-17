from flask_apispec import use_kwargs
from sqlalchemy.orm import joinedload

from webapp.helpers import filter_product_versions, is_product_active
from webapp.models import Deployment, Product
from webapp.schemas import GetProductsQuerySchema, ProductSchema


@use_kwargs(GetProductsQuerySchema, location="query")
def get_products(include_expired):
    products = Product.query.options(
        joinedload(Product.deployments).joinedload(Deployment.versions)
    ).all()
    if not include_expired:
        products = [p for p in products if is_product_active(p)]
    return {"products": ProductSchema(many=True).dump(products)}, 200


@use_kwargs(GetProductsQuerySchema, location="query")
def get_product(product_slug, include_expired):
    product = (
        Product.query.options(
            joinedload(Product.deployments).joinedload(Deployment.versions)
        )
        .filter_by(slug=product_slug)
        .one_or_none()
    )

    if product is None:
        return {
            "error": {
                "message": "Product not found.",
                "details": {"product_slug": product_slug},
            }
        }, 404

    if not include_expired:
        product = filter_product_versions(product)

    return ProductSchema().dump(product), 200
