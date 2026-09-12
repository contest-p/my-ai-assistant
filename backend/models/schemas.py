# Phase 5에서 Message/ConversationCreate 추가 예정

from pydantic import BaseModel, Field

DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"


class DataCreate(BaseModel):
    date: str = Field(pattern=DATE_PATTERN)
    value: float
    memo: str = Field(min_length=1)
    category: str | None = None


class DataUpdate(BaseModel):
    date: str | None = Field(default=None, pattern=DATE_PATTERN)
    value: float | None = None
    memo: str | None = Field(default=None, min_length=1)
    category: str | None = None
