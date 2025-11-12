"""Add source and local_path to images table

Revision ID: add_image_source_fields
Revises: 
Create Date: 2025-04-11 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_image_source_fields'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add source column with a default of 'upload' for existing records
    op.add_column('images', 
                 sa.Column('source', 
                          sa.Enum('upload', 'local_dir', 'generated', name='imagesource'), 
                          nullable=False,
                          server_default='upload'))
    
    # Add local_path column (nullable)
    op.add_column('images', 
                 sa.Column('local_path', 
                          sa.String(length=500), 
                          nullable=True))

def downgrade():
    # Drop the columns in reverse order
    op.drop_column('images', 'local_path')
    op.drop_column('images', 'source')
    
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS imagesource")
