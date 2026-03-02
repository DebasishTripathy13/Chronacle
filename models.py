from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class EntryCreate(BaseModel):
    content: str
    author: str = "anon"
    event_date: Optional[date] = None

    @field_validator("event_date", mode="before")
    @classmethod
    def parse_event_date(cls, v):
        if v is None:
            return date.today()
        if isinstance(v, str):
            v = date.fromisoformat(v)
        return v


class EntryResponse(BaseModel):
    id: int
    content: str
    author: str
    event_date: date
    created_at: datetime
