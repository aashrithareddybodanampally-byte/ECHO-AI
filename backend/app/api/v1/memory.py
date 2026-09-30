from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.memory import Memory
from app.models.user import User
from app.schemas.memory import (
    MemoryCreate,
    MemoryListResponse,
    MemoryResponse,
    SettingsResponse,
    SettingsUpdate,
)

router = APIRouter(tags=["Memory & Settings"])

MAX_MEMORIES = 50


@router.get("/memory", response_model=MemoryListResponse)
def list_memories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """View everything ECHO-AI remembers about the current user."""
    items = db.query(Memory).filter(Memory.user_id == current_user.id).order_by(Memory.id).all()
    return MemoryListResponse(enabled=current_user.memory_enabled, items=items)


@router.post("/memory", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
def add_memory(
    body: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a fact or preference the user explicitly wants remembered."""
    if not current_user.memory_enabled:
        raise HTTPException(status_code=409, detail="Memory is disabled")
    count = db.query(Memory).filter(Memory.user_id == current_user.id).count()
    if count >= MAX_MEMORIES:
        raise HTTPException(status_code=409, detail=f"Memory limit of {MAX_MEMORIES} items reached")
    memory = Memory(user_id=current_user.id, content=body.content.strip())
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


@router.delete("/memory/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memory = (
        db.query(Memory)
        .filter(Memory.id == memory_id, Memory.user_id == current_user.id)
        .first()
    )
    if memory is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(memory)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _set_memory_enabled(user: User, db: Session, enabled: bool) -> SettingsResponse:
    user.memory_enabled = enabled
    db.commit()
    db.refresh(user)
    return SettingsResponse.model_validate(user)


@router.post("/memory/disable", response_model=SettingsResponse)
def disable_memory(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Stop using saved memories in replies. Saved items are kept until deleted."""
    return _set_memory_enabled(current_user, db, False)


@router.post("/memory/enable", response_model=SettingsResponse)
def enable_memory(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _set_memory_enabled(current_user, db, True)


@router.get("/settings", response_model=SettingsResponse)
def get_settings(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/settings", response_model=SettingsResponse)
def update_settings(
    body: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user
