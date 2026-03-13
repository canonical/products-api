from flask_apispec import use_kwargs
from sqlalchemy.orm import joinedload

from webapp.helpers import is_product_active
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
