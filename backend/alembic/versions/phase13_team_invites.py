"""Phase 13: Add team_invites table for secure invite token storage

Revision ID: a2b3c4d5e6f7
Revises: f1g2h3i4j5k6
Create Date: 2026-03-02
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1g2h3i4j5k6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'team_invites',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), server_default='member'),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('invited_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_used', sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index('ix_team_invites_id', 'team_invites', ['id'])
    op.create_index('ix_team_invites_token_hash', 'team_invites', ['token_hash'])


def downgrade() -> None:
    op.drop_index('ix_team_invites_token_hash', table_name='team_invites')
    op.drop_index('ix_team_invites_id', table_name='team_invites')
    op.drop_table('team_invites')
