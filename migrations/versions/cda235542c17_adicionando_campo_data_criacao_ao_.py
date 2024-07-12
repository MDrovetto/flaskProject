"""Adicionando campo data_criacao ao modelo Answer

Revision ID: cda235542c17
Revises: 
Create Date: 2024-07-12 09:56:49.404143

"""
from alembic import op
import sqlalchemy as sa
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'cda235542c17'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Adicionar a coluna com valor padrão de tempo atual
    with op.batch_alter_table('answer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('data_criacao', sa.datetime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))

def downgrade():
    with op.batch_alter_table('answer', schema=None) as batch_op:
        batch_op.drop_column('data_criacao')