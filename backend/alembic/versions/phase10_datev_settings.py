"""add Phase 10 — DATEV settings columns to organizations

Revision ID: d9e5g1h2i3j4
Revises: c8d4f0e5a3b2
Create Date: 2026-02-28 12:00:00.000000
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd9e5g1h2i3j4'
down_revision: Union[str, None] = 'c8d4f0e5a3b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('organizations', sa.Column('datev_berater_nr', sa.String(5), nullable=True))
    op.add_column('organizations', sa.Column('datev_mandant_nr', sa.String(5), nullable=True))
    op.add_column('organizations', sa.Column('steuerberater_email', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('organizations', 'steuerberater_email')
    op.drop_column('organizations', 'datev_mandant_nr')
    op.drop_column('organizations', 'datev_berater_nr')
