"""add owner_launchpad_team to products

Revision ID: 6b9fb9564a90
Revises: d0dc7df37935
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b9fb9564a90'
down_revision: Union[str, None] = 'd0dc7df37935'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column('owner_launchpad_team', sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('products', 'owner_launchpad_team')