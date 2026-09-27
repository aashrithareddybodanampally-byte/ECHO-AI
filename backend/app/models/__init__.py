# Import all models here so that SQLAlchemy Base.metadata
# discovers them before Alembic evaluates the schema.
# Order matters: User must be imported before Conversation,
# and Conversation before Message, to satisfy FK dependencies.
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

__all__ = ["User", "Conversation", "Message"]
