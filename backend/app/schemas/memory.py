from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.rag import reject_blank


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)

    _check_content = field_validator("content")(reject_blank)


class MemoryResponse(BaseModel):
    id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryListResponse(BaseModel):
    enabled: bool
    items: list[MemoryResponse]


ResponseStyle = Literal["concise", "balanced", "detailed"]


class SettingsResponse(BaseModel):
    memory_enabled: bool
    save_emotion_stats: bool
    response_style: ResponseStyle

    model_config = ConfigDict(from_attributes=True)


class SettingsUpdate(BaseModel):
    memory_enabled: bool | None = None
    save_emotion_stats: bool | None = None
    response_style: ResponseStyle | None = None
