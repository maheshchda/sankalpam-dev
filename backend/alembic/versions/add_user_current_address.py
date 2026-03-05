"""Add current_city, current_state, current_country to users (current address)

Revision ID: add_user_current_address
Revises: add_nakshatra_rashi
Create Date: 2025-02-13

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_user_current_address'
down_revision = 'add_nakshatra_rashi'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('current_city', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('current_state', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('current_country', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'current_country')
    op.drop_column('users', 'current_state')
    op.drop_column('users', 'current_city')
