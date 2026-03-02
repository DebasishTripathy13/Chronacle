from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException

import database as db
from models import EntryCreate, EntryResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.database.connect()
    await db.init_db()
    yield
    await db.database.disconnect()


app = FastAPI(
    title="Time Traveler API — Hawking's Party",
    description=(
        "Inspired by Stephen Hawking's 2009 time traveler party: he hosted it, then sent "
        "invitations *after* it ended — so only a real time traveler would have known to attend. "
        "This API lets you post entries to any past date. If a time traveler from the future "
        "wants to post to yesterday's database, the infrastructure is already here for them."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Time Traveler API — Hawking's Party Edition",
        "concept": (
            "Stephen Hawking hosted a party for time travelers in 2009, then sent invitations "
            "after it ended. Only a genuine time traveler would have known to attend. "
            "This API works the same way: post entries to any past date. "
            "The infrastructure exists now — so if you're from the future, you're welcome."
        ),
        "endpoints": {
            "POST /entries": "Write an entry to any past or present date",
            "GET /entries/{date}": "Read all entries for a specific date (YYYY-MM-DD)",
            "GET /entries": "List all entries, sorted by event_date descending",
            "GET /docs": "Interactive Swagger UI",
        },
    }


@app.post("/entries", response_model=EntryResponse, status_code=201)
async def create_entry(body: EntryCreate):
    row = await db.create_entry(
        content=body.content,
        author=body.author,
        event_date=body.event_date,
    )
    return row


@app.get("/entries/{date}", response_model=list[EntryResponse])
async def get_entries_by_date(date: date):
    rows = await db.get_entries_by_date(date)
    return rows


@app.get("/entries", response_model=list[EntryResponse])
async def list_entries(
    author: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    rows = await db.get_all_entries(limit=limit, offset=offset, author=author)
    return rows
