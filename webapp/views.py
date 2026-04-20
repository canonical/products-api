from datetime import date

from flask_apispec import use_kwargs
from sqlalchemy.orm import joinedload

from webapp.database import db
from webapp.helpers import (
    filter_deployment_versions,
    filter_product_versions,
    is_product_active,
    slugify,
    validate_dates_after_release,
)
from webapp.models import Deployment, Product, Version
from webapp.schemas import (
    CreateVersionBodySchema,
    CreateProductDeploymentBodySchema,
    CreateProductBodySchema,
    DeploymentSchema,
    GetProductsQuerySchema,
    ProductSchema,
    UpdateProductDeploymentBodySchema,
    UpdateProductBodySchema,
    UpdateVersionBodySchema,
    VersionSchema,
)


@use_kwargs(GetProductsQuerySchema, location="query")
def get_products(include_expired, include_hidden):
    products = Product.query.options(
        joinedload(Product.deployments).joinedload(Deployment.versions)
    ).all()
    if not include_expired:
        products = [
            p
            for p in products
            if is_product_active(p, include_hidden=include_hidden)
        ]
    filtered = [
        filter_product_versions(
            p,
            include_expired=include_expired,
            include_hidden=include_hidden,
        )
        for p in products
    ]
    return {"products": ProductSchema(many=True).dump(filtered)}, 200


@use_kwargs(GetProductsQuerySchema, location="query")
def get_product(product_slug, include_expired, include_hidden):
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

    product = filter_product_versions(
        product,
        include_expired=include_expired,
        include_hidden=include_hidden,
    )

    return ProductSchema().dump(product), 200


@use_kwargs(GetProductsQuerySchema, location="query")
def get_product_deployment(
    product_slug, deployment_slug, include_expired, include_hidden
):
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

    deployment = filter_deployment_versions(
        deployment,
        include_expired=include_expired,
        include_hidden=include_hidden,
    )

    return DeploymentSchema().dump(deployment), 200


def get_product_deployment_version(product_slug, deployment_slug, release):
    version = Version.query.filter_by(
        parent_product=product_slug,
        parent_deployment=deployment_slug,
        release=release,
    ).one_or_none()

    if version is None:
        return {
            "error": {
                "message": "Version not found.",
                "details": {
                    "product_slug": product_slug,
                    "deployment_slug": deployment_slug,
                    "release": release,
                },
            }
        }, 404

    return VersionSchema().dump(version), 200


@use_kwargs(CreateProductBodySchema, location="json")
def create_product(name, deployments):
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
        deployment = Deployment(
            slug=slugify(dep_data["name"]),
            parent_product=slug,
            name=dep_data["name"],
            artifact_type=dep_data["artifact_type"],
        )
        db.session.add(deployment)

    try:
        db.session.commit()
    except Exception:
        db.session.remove()
        return {
            "error": {
                "message": "Product or deployment slug already exists.",
                "details": {"product_slug": slug},
            }
        }, 409

    return ProductSchema().dump(product), 201


@use_kwargs(CreateProductDeploymentBodySchema, location="json")
def create_product_deployment(product_slug, name, artifact_type):
    product = Product.query.filter_by(slug=product_slug).one_or_none()
    if product is None:
        return {
            "error": {
                "message": "Product not found.",
                "details": {"product_slug": product_slug},
            }
        }, 404

    slug = slugify(name)

    existing_deployment = Deployment.query.filter_by(
        parent_product=product_slug,
        slug=slug,
    ).one_or_none()
    if existing_deployment is not None:
        return {
            "error": {
                "message": "Deployment already exists.",
                "details": {
                    "product_slug": product_slug,
                    "deployment_slug": slug,
                },
            }
        }, 409

    deployment = Deployment(
        slug=slug,
        parent_product=product_slug,
        name=name,
        artifact_type=artifact_type,
    )
    db.session.add(deployment)

    try:
        db.session.commit()
    except Exception:
        db.session.remove()
        return {
            "error": {
                "message": "Internal server error.",
                "details": {},
            }
        }, 500

    return DeploymentSchema().dump(deployment), 201


@use_kwargs(CreateVersionBodySchema, location="json")
def create_version(
    product_slug,
    deployment_slug,
    release,
    architecture,
    release_date,
    supported,
    esm_pro_supported,
    break_bug_pro_supported,
    legacy_supported,
    upgrade_path=None,
    compatible_ubuntu_lts=None,
    is_hidden=False,
):
    product = Product.query.filter_by(slug=product_slug).one_or_none()
    if product is None:
        return {
            "error": {
                "message": "Product not found.",
                "details": {"product_slug": product_slug},
            }
        }, 404

    deployment = Deployment.query.filter_by(
        parent_product=product_slug,
        slug=deployment_slug,
    ).one_or_none()
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

    existing_version = Version.query.filter_by(
        parent_product=product_slug,
        parent_deployment=deployment_slug,
        release=release,
    ).one_or_none()
    if existing_version is not None:
        return {
            "error": {
                "message": "Version already exists.",
                "details": {
                    "product_slug": product_slug,
                    "deployment_slug": deployment_slug,
                    "release": release,
                },
            }
        }, 409

    version = Version(
        parent_product=product_slug,
        parent_deployment=deployment_slug,
        release=release,
        architecture=architecture,
        release_date=release_date,
        supported=supported,
        esm_pro_supported=esm_pro_supported,
        break_bug_pro_supported=break_bug_pro_supported,
        legacy_supported=legacy_supported,
        upgrade_path=upgrade_path,
        compatible_ubuntu_lts=compatible_ubuntu_lts,
        is_hidden=is_hidden,
    )
    db.session.add(version)

    try:
        db.session.commit()
    except Exception:
        db.session.remove()
        return {
            "error": {
                "message": "Internal server error.",
                "details": {},
            }
        }, 500

    return VersionSchema().dump(version), 201


@use_kwargs(UpdateProductBodySchema, location="json")
def update_product(product_slug, name):
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

    product.name = name
    try:
        db.session.commit()
    except Exception:
        db.session.remove()
        return {
            "error": {
                "message": "Internal server error.",
                "details": {},
            }
        }, 500

    return ProductSchema().dump(product), 200


@use_kwargs(UpdateProductDeploymentBodySchema, location="json")
def update_product_deployment(
    product_slug,
    deployment_slug,
    name=None,
    artifact_type=None,
):
    product = Product.query.filter_by(slug=product_slug).one_or_none()
    if product is None:
        return {
            "error": {
                "message": "Product not found.",
                "details": {"product_slug": product_slug},
            }
        }, 404

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

    if name is not None:
        deployment.name = name
    if artifact_type is not None:
        deployment.artifact_type = artifact_type

    try:
        db.session.commit()
    except Exception:
        db.session.remove()
        return {
            "error": {
                "message": "Internal server error.",
                "details": {},
            }
        }, 500

    return DeploymentSchema().dump(deployment), 200


@use_kwargs(UpdateVersionBodySchema, location="json")
def update_version(product_slug, deployment_slug, release, **data):
    product = Product.query.filter_by(slug=product_slug).one_or_none()
    if product is None:
        return {
            "error": {
                "message": "Product not found.",
                "details": {"product_slug": product_slug},
            }
        }, 404

    deployment = Deployment.query.filter_by(
        parent_product=product_slug,
        slug=deployment_slug,
    ).one_or_none()

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

    version = Version.query.filter_by(
        parent_product=product_slug,
        parent_deployment=deployment_slug,
        release=release,
    ).one_or_none()

    if version is None:
        return {
            "error": {
                "message": "Version not found.",
                "details": {
                    "product_slug": product_slug,
                    "deployment_slug": deployment_slug,
                    "release": release,
                },
            }
        }, 404

    effective_release_date_str = (
        data.get("release_date", {}) or {}
    ).get("date") or (version.release_date or {}).get("date")

    if effective_release_date_str:
        try:
            effective_release_date = date.fromisoformat(
                effective_release_date_str
            )
        except (TypeError, ValueError):
            effective_release_date = None

        if effective_release_date:
            lifecycle_fields = {
                "supported": data.get(
                    "supported", version.supported or {}
                ),
                "esm_pro_supported": data.get(
                    "esm_pro_supported",
                    version.esm_pro_supported or {},
                ),
                "break_bug_pro_supported": data.get(
                    "break_bug_pro_supported",
                    version.break_bug_pro_supported or {},
                ),
                "legacy_supported": data.get(
                    "legacy_supported",
                    version.legacy_supported or {},
                ),
            }
            errors = validate_dates_after_release(
                effective_release_date, lifecycle_fields
            )
            if errors:
                return {
                    "error": {
                        "message": "Invalid request.",
                        "details": errors,
                    }
                }, 400

    for field, value in data.items():
        setattr(version, field, value)

    try:
        db.session.commit()
    except Exception:
        db.session.remove()
        return {
            "error": {
                "message": "Internal server error.",
                "details": {},
            }
        }, 500

    return VersionSchema().dump(version), 200
