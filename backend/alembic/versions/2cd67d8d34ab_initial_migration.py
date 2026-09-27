"""Initial migration

Revision ID: 2cd67d8d34ab
Revises: 
Create Date: 2026-09-28 00:27:29.065811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cd67d8d34ab'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This initial migration is intentionally empty.
    # It establishes the Alembic version tracking table.
    # Future phases (Phase 2.3+) will introduce application models like User, Conversation, etc.,
    # at which point subsequent migrations will contain table creation logic.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
