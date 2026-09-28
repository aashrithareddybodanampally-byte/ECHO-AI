"""Add hashed_password to User

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the column as nullable=True
    op.add_column('users', sa.Column('hashed_password', sa.String(length=255), nullable=True))
    
    # 2. Backfill existing records with a valid placeholder bcrypt hash
    # (This ensures existing pre-production users don't break the application)
    dummy_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYq"
    op.execute(f"UPDATE users SET hashed_password = '{dummy_hash}' WHERE hashed_password IS NULL")
    
    # 3. Alter the column to NOT NULL
    op.alter_column('users', 'hashed_password', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'hashed_password')
