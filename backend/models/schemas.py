from datetime import date

from pydantic import BaseModel, Field, field_validator

DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"


class DataCreate(BaseModel):
    date: str = Field(pattern=DATE_PATTERN)
    value: float = Field(allow_inf_nan=False)
    memo: str = Field(min_length=1)
    category: str | None = None

    @field_validator("date")
    @classmethod
    def valid_date(cls, value):
        date.fromisoformat(value)
        return value

    @field_validator("memo")
    @classmethod
    def nonblank_memo(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("내용을 입력해주세요.")
        return value


class DataUpdate(BaseModel):
    date: str | None = Field(default=None, pattern=DATE_PATTERN)
    value: float | None = Field(default=None, allow_inf_nan=False)
    memo: str | None = Field(default=None, min_length=1)
    category: str | None = None

    @field_validator("date", "value", "memo", mode="before")
    @classmethod
    def reject_explicit_null(cls, value):
        # 부분 수정에서 생략은 허용하지만 필수 거래 필드를 null로 지울 수는 없다.
        if value is None:
            raise ValueError("필수 거래 필드는 null로 변경할 수 없습니다.")
        return value

    @field_validator("date")
    @classmethod
    def valid_date(cls, value):
        return DataCreate.valid_date(value)

    @field_validator("memo")
    @classmethod
    def nonblank_memo(cls, value):
        return DataCreate.nonblank_memo(value)


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

    @field_validator("message")
    @classmethod
    def nonblank_message(cls, value):
        return DataCreate.nonblank_memo(value)
