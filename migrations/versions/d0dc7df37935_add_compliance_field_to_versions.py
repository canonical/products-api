"""add compliance field to versions

Revision ID: d0dc7df37935
Revises: 0aa283fddc29
Create Date: 2026-06-16 19:39:09.938221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0dc7df37935'
down_revision: Union[str, None] = '0aa283fddc29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'versions',
        sa.Column('compliance', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('versions', 'compliance')
