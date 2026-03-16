"""Add is_married to family_members

Revision ID: add_is_married
Revises: add_cancelled_invitees
Create Date: 2026-03-20

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_is_married'
down_revision = 'add_cancelled_invitees'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('family_members', sa.Column('is_married', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('family_members', 'is_married')
