"""
Chronacle — TimeBoard
Every date has a feed. Posts can arrive from any point in time.
"""

import sqlite3
import asyncio
import json
from datetime import datetime, timezone, date
from contextlib import asynccontextmanager
from collections import defaultdict
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# live subscribers: date_string -> list of queues
subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

DB_PATH = "oracle.db"


# --- Database ---

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            content    TEXT NOT NULL,
            author     TEXT NOT NULL DEFAULT 'anon',
            for_date   DATE NOT NULL,
            written_at DATETIME NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_for_date ON posts(for_date)")
    conn.commit()
    conn.close()


# --- Models ---

class PostIn(BaseModel):
    content: str
    author: str = "anon"
    for_date: date


# --- App ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Chronacle — TimeBoard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse("static/home.html")


@app.get("/board", include_in_schema=False)
def frontend():
    return FileResponse("static/index.html")


@app.post("/post", status_code=201)
def create_post(body: PostIn):
    if body.for_date > date.today():
        raise HTTPException(status_code=400, detail="Cannot post to a future date.")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO posts (content, author, for_date, written_at) VALUES (?, ?, ?, ?)",
        (body.content, body.author, body.for_date.isoformat(), now.isoformat()),
    )
    conn.commit()
    conn.close()

    post = {
        "id": cur.lastrowid,
        "content": body.content,
        "author": body.author,
        "for_date": body.for_date.isoformat(),
        "written_at": now.isoformat(),
    }

    # push to anyone currently listening on this date
    for queue in subscribers[body.for_date.isoformat()]:
        queue.put_nowait(post)

    return post


@app.get("/feed/{for_date}")
def get_feed(for_date: date, limit: int = 50, offset: int = 0):
    if for_date > date.today():
        raise HTTPException(status_code=400, detail="Cannot access a future date.")
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM posts WHERE for_date = ? ORDER BY written_at DESC LIMIT ? OFFSET ?",
        (for_date.isoformat(), limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/stream/{for_date}")
async def stream(for_date: date):
    """SSE endpoint — push new posts to connected clients in real time."""
    if for_date > date.today():
        raise HTTPException(status_code=400, detail="Cannot stream a future date.")
    queue: asyncio.Queue = asyncio.Queue()
    date_key = for_date.isoformat()
    subscribers[date_key].append(queue)

    async def events() -> AsyncGenerator[str, None]:
        try:
            while True:
                post = await queue.get()
                yield f"data: {json.dumps(post)}\n\n"
        finally:
            if queue in subscribers[date_key]:
                subscribers[date_key].remove(queue)

    return StreamingResponse(events(), media_type="text/event-stream")


@app.get("/dates")
def active_dates():
    """Returns dates that have posts, with counts — for the sidebar."""
    conn = get_db()
    rows = conn.execute(
        "SELECT for_date, COUNT(*) as count FROM posts GROUP BY for_date ORDER BY for_date DESC LIMIT 30"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
