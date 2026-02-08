"""Add birth_time to family_members

Revision ID: add_birth_time_family
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_birth_time_family'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add birth_time column with default value for existing records
    op.add_column('family_members', sa.Column('birth_time', sa.String(length=10), nullable=False, server_default='00:00'))


def downgrade() -> None:
    op.drop_column('family_members', 'birth_time')

