"""
User domain model.

Represents a human interacting with ECHO-AI. This is the identity
anchor for conversations and future personalization features.

Phase 2.3: Minimal identity model only.
Authentication, password hashing, and tokens are deferred to Phase 2.4+.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class User(Base):
    """
    Persistent domain model for a registered ECHO-AI user.

    Columns
    -------
    id          : Integer surrogate primary key.
    email       : Unique, non-null login identifier.
    created_at  : UTC timestamp set automatically at insert time.
    updated_at  : UTC timestamp updated automatically on every modification.

    Relationships
    -------------
    conversations : One-to-many; all Conversation records owned by this user.
    """

    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
