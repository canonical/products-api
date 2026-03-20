from flask_apispec import use_kwargs
from sqlalchemy.orm import joinedload

from webapp.database import db
from webapp.helpers import (
    filter_deployment_versions,
    filter_product_versions,
    is_product_active,
    slugify,
)
from webapp.models import Deployment, Product
from webapp.schemas import (
    CreateProductBodySchema,
    DeploymentSchema,
    GetProductsQuerySchema,
    ProductSchema,
)


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


@use_kwargs(GetProductsQuerySchema, location="query")
def get_product_deployment(product_slug, deployment_slug, include_expired):
    deployment = (
        Deployment.query.options(joinedload(Deployment.versions))
        .filter_by(
            parent_product=product_slug,
            slug=deployment_slug,
        )
        .one_or_none()
    )

    if deployment is None:
        return {
            "error": {
                "message": "Deployment not found.",
                "details": {
                    "product_slug": product_slug,
                    "deployment_slug": deployment_slug,
                },
            }
        }, 404

    if not include_expired:
        deployment = filter_deployment_versions(deployment)

    return DeploymentSchema().dump(deployment), 200


@use_kwargs(CreateProductBodySchema, location="json")
def create_product(slug, name, deployments):
    if slug is None:
        slug = slugify(name)

    existing_product = Product.query.filter_by(slug=slug).one_or_none()
    if existing_product:
        return {
            "error": {
                "message": "Product or deployment slug already exists.",
                "details": {"product_slug": slug},
            }
        }, 409

    product = Product(slug=slug, name=name)
    db.session.add(product)

    for dep_data in deployments:
        dep_slug = dep_data["slug"]
        if dep_slug is None:
            dep_slug = slugify(dep_data["name"])
        
        deployment = Deployment(
            slug=dep_slug,
            parent_product=slug,
            name=dep_data["name"],
            artifact_type=dep_data["artifact_type"],
        )
        db.session.add(deployment)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return {
            "error": {
                "message": "Product or deployment slug already exists.",
                "details": {"product_slug": slug},
            }
        }, 409

    return ProductSchema().dump(product), 201
