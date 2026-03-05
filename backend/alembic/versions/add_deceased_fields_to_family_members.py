"""add deceased fields to family members

Revision ID: add_deceased_fields
Revises:
Create Date: 2026-02-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_deceased_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('family_members', sa.Column('is_deceased',   sa.Boolean(),     nullable=False, server_default='0'))
    op.add_column('family_members', sa.Column('date_of_death', sa.DateTime(),     nullable=True))
    op.add_column('family_members', sa.Column('time_of_death', sa.String(10),     nullable=True))
    op.add_column('family_members', sa.Column('death_city',    sa.String(100),    nullable=True))
    op.add_column('family_members', sa.Column('death_state',   sa.String(100),    nullable=True))
    op.add_column('family_members', sa.Column('death_country', sa.String(100),    nullable=True))


def downgrade():
    op.drop_column('family_members', 'death_country')
    op.drop_column('family_members', 'death_state')
    op.drop_column('family_members', 'death_city')
    op.drop_column('family_members', 'time_of_death')
    op.drop_column('family_members', 'date_of_death')
    op.drop_column('family_members', 'is_deceased')
