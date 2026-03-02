from datetime import date, datetime, timezone
from typing import Optional

import databases
import sqlalchemy

DATABASE_URL = "sqlite+aiosqlite:///./time_traveler.db"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

entries = sqlalchemy.Table(
    "entries",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("content", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("author", sqlalchemy.Text, nullable=False, default="anon"),
    sqlalchemy.Column("event_date", sqlalchemy.Date, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, nullable=False),
)

engine = sqlalchemy.create_engine(DATABASE_URL.replace("+aiosqlite", ""))


async def init_db():
    metadata.create_all(engine)


async def create_entry(content: str, author: str, event_date: date) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    query = entries.insert().values(
        content=content,
        author=author,
        event_date=event_date,
        created_at=now,
    )
    row_id = await database.execute(query)
    return {
        "id": row_id,
        "content": content,
        "author": author,
        "event_date": event_date,
        "created_at": now,
    }


async def get_entries_by_date(event_date: date) -> list[dict]:
    query = entries.select().where(entries.c.event_date == event_date)
    rows = await database.fetch_all(query)
    return [dict(row) for row in rows]


async def get_all_entries(
    limit: int = 20,
    offset: int = 0,
    author: Optional[str] = None,
) -> list[dict]:
    query = entries.select().order_by(entries.c.event_date.desc())
    if author is not None:
        query = query.where(entries.c.author == author)
    query = query.limit(limit).offset(offset)
    rows = await database.fetch_all(query)
    return [dict(row) for row in rows]
