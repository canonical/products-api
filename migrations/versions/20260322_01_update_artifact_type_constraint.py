"""update deployments artifact type constraint

Revision ID: 20260322_01
Revises: 20260223_01
Create Date: 2026-03-22
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260322_01"
down_revision = "20260223_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_deployments_artifact_type", "deployments", type_="check"
    )
    op.create_check_constraint(
        "ck_deployments_artifact_type",
        "deployments",
        "artifact_type IN ('snap', 'deb', 'charm', 'image', 'rock', 'other')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_deployments_artifact_type", "deployments", type_="check"
    )
    op.create_check_constraint(
        "ck_deployments_artifact_type",
        "deployments",
        "artifact_type IN ('snap', 'deb', 'charm', 'image', 'container', 'other')",
    )