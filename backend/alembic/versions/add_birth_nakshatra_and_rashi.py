"""Add birth_nakshatra and birth_rashi to users and family_members

Revision ID: add_nakshatra_rashi
Revises: add_birth_time_family
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_nakshatra_rashi'
down_revision = 'add_birth_time_family'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add birth_nakshatra and birth_rashi to users table
    op.add_column('users', sa.Column('birth_nakshatra', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('birth_rashi', sa.String(length=50), nullable=True))
    
    # Add birth_nakshatra and birth_rashi to family_members table
    op.add_column('family_members', sa.Column('birth_nakshatra', sa.String(length=50), nullable=True))
    op.add_column('family_members', sa.Column('birth_rashi', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Remove columns from family_members
    op.drop_column('family_members', 'birth_rashi')
    op.drop_column('family_members', 'birth_nakshatra')
    
    # Remove columns from users
    op.drop_column('users', 'birth_rashi')
    op.drop_column('users', 'birth_nakshatra')
