"""Add image_type column to images table

Revision ID: 1234567890ab
Revises: <previous_migration_id>
Create Date: 2025-11-13 12:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1234567890ab'
down_revision = None  # Replace with the previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Add the image_type column with a default value of 'general'
    op.add_column('images', sa.Column('image_type', sa.Enum('general', 'advertising_campaign', name='imagetype'), 
                  server_default='general', nullable=False))


def downgrade():
    # Remove the image_type column
    op.drop_column('images', 'image_type')
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS imagetype")
