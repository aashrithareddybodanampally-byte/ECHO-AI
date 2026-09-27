"""
Unit tests for Phase 2.3 domain models.

These tests do NOT require a live PostgreSQL server.
They verify:
  - Model instantiation and field defaults
  - SQLAlchemy metadata registration (Base.metadata)
  - Relationship configuration
  - Column-level constraints (nullability, type, FK targets)
  - MessageRole enum values

All assertions use SQLAlchemy's metadata inspection API, not live DB queries.
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect as sa_inspect

from app.db.base import Base
import app.models  # noqa: F401 — ensures models register with Base.metadata
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_column(table, col_name):
    """Return a Column object from a SQLAlchemy Table by name."""
    return table.c[col_name]


def _get_table(model_class):
    """Return the mapped Table object for a model class."""
    return model_class.__table__


# ---------------------------------------------------------------------------
# Base.metadata registration
# ---------------------------------------------------------------------------

class TestMetadataRegistration:
    """Verify all three models appear in Base.metadata.tables."""

    def test_users_table_registered(self):
        assert "users" in Base.metadata.tables, "users table missing from Base.metadata"

    def test_conversations_table_registered(self):
        assert "conversations" in Base.metadata.tables, "conversations table missing from Base.metadata"

    def test_messages_table_registered(self):
        assert "messages" in Base.metadata.tables, "messages table missing from Base.metadata"


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

class TestUserModel:
    """Tests for the User domain model."""

    def test_user_can_be_instantiated(self):
        user = User(email="test@example.com")
        assert user is not None

    def test_user_email_field_exists(self):
        table = _get_table(User)
        assert "email" in table.c

    def test_user_id_is_primary_key(self):
        table = _get_table(User)
        pk_cols = [c.name for c in table.primary_key.columns]
        assert "id" in pk_cols

    def test_user_email_is_not_nullable(self):
        col = _get_column(_get_table(User), "email")
        assert col.nullable is False

    def test_user_email_unique_constraint_exists(self):
        table = _get_table(User)
        unique_constraint_names = [
            c.name for c in table.constraints
            if hasattr(c, "columns") and "email" in [col.name for col in c.columns]
        ]
        assert len(unique_constraint_names) > 0, "No unique constraint found on users.email"

    def test_user_created_at_is_not_nullable(self):
        col = _get_column(_get_table(User), "created_at")
        assert col.nullable is False

    def test_user_updated_at_is_not_nullable(self):
        col = _get_column(_get_table(User), "updated_at")
        assert col.nullable is False

    def test_user_has_conversations_relationship(self):
        mapper = sa_inspect(User)
        rel_names = [r.key for r in mapper.relationships]
        assert "conversations" in rel_names

    def test_user_repr(self):
        user = User(id=1, email="repr@example.com")
        assert "repr@example.com" in repr(user)


# ---------------------------------------------------------------------------
# Conversation model
# ---------------------------------------------------------------------------

class TestConversationModel:
    """Tests for the Conversation domain model."""

    def test_conversation_can_be_instantiated(self):
        conv = Conversation(user_id=1, title="Test Session")
        assert conv is not None

    def test_conversation_id_is_primary_key(self):
        table = _get_table(Conversation)
        pk_cols = [c.name for c in table.primary_key.columns]
        assert "id" in pk_cols

    def test_conversation_user_id_is_not_nullable(self):
        col = _get_column(_get_table(Conversation), "user_id")
        assert col.nullable is False

    def test_conversation_user_id_fk_points_to_users(self):
        col = _get_column(_get_table(Conversation), "user_id")
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "users.id" in fk_targets, f"FK target mismatch: {fk_targets}"

    def test_conversation_title_is_nullable(self):
        col = _get_column(_get_table(Conversation), "title")
        assert col.nullable is True

    def test_conversation_has_user_relationship(self):
        mapper = sa_inspect(Conversation)
        rel_names = [r.key for r in mapper.relationships]
        assert "user" in rel_names

    def test_conversation_has_messages_relationship(self):
        mapper = sa_inspect(Conversation)
        rel_names = [r.key for r in mapper.relationships]
        assert "messages" in rel_names

    def test_conversation_created_at_is_not_nullable(self):
        col = _get_column(_get_table(Conversation), "created_at")
        assert col.nullable is False

    def test_conversation_updated_at_is_not_nullable(self):
        col = _get_column(_get_table(Conversation), "updated_at")
        assert col.nullable is False

    def test_conversation_repr(self):
        conv = Conversation(id=5, user_id=1, title="My chat")
        assert "5" in repr(conv)


# ---------------------------------------------------------------------------
# Message model
# ---------------------------------------------------------------------------

class TestMessageModel:
    """Tests for the Message domain model."""

    def test_message_can_be_instantiated(self):
        msg = Message(conversation_id=1, role="user", content="Hello, ECHO!")
        assert msg is not None

    def test_message_id_is_primary_key(self):
        table = _get_table(Message)
        pk_cols = [c.name for c in table.primary_key.columns]
        assert "id" in pk_cols

    def test_message_conversation_id_is_not_nullable(self):
        col = _get_column(_get_table(Message), "conversation_id")
        assert col.nullable is False

    def test_message_conversation_id_fk_points_to_conversations(self):
        col = _get_column(_get_table(Message), "conversation_id")
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "conversations.id" in fk_targets, f"FK target mismatch: {fk_targets}"

    def test_message_role_is_not_nullable(self):
        col = _get_column(_get_table(Message), "role")
        assert col.nullable is False

    def test_message_content_is_not_nullable(self):
        col = _get_column(_get_table(Message), "content")
        assert col.nullable is False

    def test_message_has_no_updated_at(self):
        """Messages are append-only; updated_at must not exist."""
        table = _get_table(Message)
        assert "updated_at" not in table.c, "Messages must not have updated_at (immutable records)"

    def test_message_has_conversation_relationship(self):
        mapper = sa_inspect(Message)
        rel_names = [r.key for r in mapper.relationships]
        assert "conversation" in rel_names

    def test_message_check_constraint_exists(self):
        table = _get_table(Message)
        check_names = [c.name for c in table.constraints if hasattr(c, "sqltext")]
        assert "ck_messages_role_valid" in check_names, (
            f"CHECK constraint 'ck_messages_role_valid' not found. Found: {check_names}"
        )

    def test_message_repr(self):
        msg = Message(id=10, role="assistant", conversation_id=2)
        assert "assistant" in repr(msg)


# ---------------------------------------------------------------------------
# MessageRole enum
# ---------------------------------------------------------------------------

class TestMessageRoleEnum:
    """Tests for the MessageRole controlled vocabulary."""

    def test_role_user_value(self):
        assert MessageRole.USER.value == "user"

    def test_role_assistant_value(self):
        assert MessageRole.ASSISTANT.value == "assistant"

    def test_role_system_value(self):
        assert MessageRole.SYSTEM.value == "system"

    def test_role_enum_is_string_subclass(self):
        assert issubclass(MessageRole, str)

    def test_only_three_roles_defined(self):
        assert len(MessageRole) == 3
