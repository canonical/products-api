"""add product resource tables

Revision ID: 20260223_01
Revises: 
Create Date: 2026-02-23
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260223_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("slug", name="pk_products"),
    )

    op.create_table(
        "deployments",
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("parent_product", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("artifact_type", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "artifact_type IN ('snap', 'deb', 'charm', 'image', 'container', 'other')",
            name="ck_deployments_artifact_type",
        ),
        sa.ForeignKeyConstraint(
            ["parent_product"], ["products.slug"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint(
            "parent_product", "slug", name="pk_deployments"
        ),
    )
    op.create_index(
        "ix_deployments_parent_product", "deployments", ["parent_product"]
    )

    op.create_table(
        "versions",
        sa.Column("parent_product", sa.String(length=100), nullable=False),
        sa.Column("parent_deployment", sa.String(length=100), nullable=False),
        sa.Column("release", sa.String(length=64), nullable=False),
        sa.Column("architecture", sa.JSON(), nullable=False),
        sa.Column("release_date", sa.JSON(), nullable=False),
        sa.Column("supported", sa.JSON(), nullable=False),
        sa.Column("pro_supported", sa.JSON(), nullable=False),
        sa.Column("legacy_supported", sa.JSON(), nullable=False),
        sa.Column("upgrade_path", sa.JSON(), nullable=True),
        sa.Column("compatible_ubuntu_lts", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_product", "parent_deployment"],
            ["deployments.parent_product", "deployments.slug"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "parent_product",
            "parent_deployment",
            "release",
            name="pk_versions",
        ),
    )
    op.create_index(
        "ix_versions_parent_product_parent_deployment",
        "versions",
        ["parent_product", "parent_deployment"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_versions_parent_product_parent_deployment", table_name="versions"
    )
    op.drop_table("versions")

    op.drop_index("ix_deployments_parent_product", table_name="deployments")
    op.drop_table("deployments")

    op.drop_table("products")
