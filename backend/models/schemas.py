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


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: str | None = None


class ConversationCreate(BaseModel):
    title: str | None = None
    messages: list[Message]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
