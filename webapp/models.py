import re

from webapp.app import db
from webapp.constants import ARTIFACT_TYPES


ARTIFACT_TYPES_SQL = ", ".join(f"'{artifact}'" for artifact in ARTIFACT_TYPES)


def _slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


class Product(db.Model):
    __tablename__ = "products"

    slug = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    deployments = db.relationship(
        "Deployment",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Deployment(db.Model):
    __tablename__ = "deployments"

    __table_args__ = (
        db.CheckConstraint(
            f"artifact_type IN ({ARTIFACT_TYPES_SQL})",
            name="ck_deployments_artifact_type",
        ),
    )

    slug = db.Column(db.String(100), primary_key=True)
    parent_product = db.Column(
        db.String(100),
        db.ForeignKey("products.slug", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    name = db.Column(db.String(255), nullable=False)
    artifact_type = db.Column(db.String(32), nullable=False)
    product = db.relationship("Product", back_populates="deployments")
    versions = db.relationship(
        "Version",
        back_populates="deployment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Version(db.Model):
    __tablename__ = "versions"

    __table_args__ = (
        db.ForeignKeyConstraint(
            ["parent_product", "parent_deployment"],
            ["deployments.parent_product", "deployments.slug"],
            ondelete="CASCADE",
        ),
    )

    parent_product = db.Column(db.String(100), primary_key=True)
    parent_deployment = db.Column(
        db.String(100),
        primary_key=True,
        nullable=False,
    )
    release = db.Column(db.String(64), primary_key=True)
    architecture = db.Column(db.JSON, nullable=False)
    release_date = db.Column(db.JSON, nullable=False)
    supported = db.Column(db.JSON, nullable=False)
    pro_supported = db.Column(db.JSON, nullable=False)
    legacy_supported = db.Column(db.JSON, nullable=False)
    upgrade_path = db.Column(db.JSON, nullable=True)
    compatible_ubuntu_lts = db.Column(db.JSON, nullable=True)

    deployment = db.relationship("Deployment", back_populates="versions")


@db.event.listens_for(Product, "before_insert")
def generate_product_slug(_, __, target):
    if not target.slug and target.name:
        target.slug = _slugify(target.name)


@db.event.listens_for(Deployment, "before_insert")
def generate_deployment_slug(_, __, target):
    if not target.slug and target.name:
        target.slug = _slugify(target.name)
