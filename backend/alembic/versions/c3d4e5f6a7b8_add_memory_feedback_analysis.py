"""add user preferences, memories, feedback and analysis results

Non-destructive: new user columns are added with server defaults (existing
rows are filled automatically); everything else is new tables.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6g7
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("memory_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("save_emotion_stats", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("response_style", sa.String(20), nullable=False, server_default="balanced"))

    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_memories_id", "memories", ["id"])
    op.create_index("ix_memories_user_id", "memories", ["user_id"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("helpful", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("message_id", name="uq_feedback_message_id"),
    )
    op.create_index("ix_feedback_id", "feedback", ["id"])
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("voice_emotion", sa.String(50), nullable=True),
        sa.Column("voice_confidence", sa.Float(), nullable=True),
        sa.Column("text_sentiment", sa.String(50), nullable=True),
        sa.Column("text_emotion", sa.String(50), nullable=True),
        sa.Column("text_confidence", sa.Float(), nullable=True),
        sa.Column("fused_state", sa.String(50), nullable=False),
        sa.Column("fused_confidence", sa.Float(), nullable=False),
        sa.Column("safety_level", sa.String(20), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("message_id", name="uq_analysis_results_message_id"),
    )
    op.create_index("ix_analysis_results_id", "analysis_results", ["id"])
    op.create_index("ix_analysis_results_user_id", "analysis_results", ["user_id"])


def downgrade() -> None:
    op.drop_table("analysis_results")
    op.drop_table("feedback")
    op.drop_table("memories")
    op.drop_column("users", "response_style")
    op.drop_column("users", "save_emotion_stats")
    op.drop_column("users", "memory_enabled")
