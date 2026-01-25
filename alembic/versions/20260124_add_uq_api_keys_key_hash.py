"""add unique constraint to api_keys.key_hash

Revision ID: 20260124_add_uq_api_keys_key_hash
Revises: 
Create Date: 2026-01-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260124_uq_api_keys'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # add unique constraint on api_keys.key_hash
    op.create_unique_constraint('uq_api_keys_key_hash', 'api_keys', ['key_hash'])


def downgrade():
    op.drop_constraint('uq_api_keys_key_hash', 'api_keys', type_='unique')
