<p align="center">
  <img src="https://img.shields.io/badge/Chronacle-TimeBoard-7c3aed?style=for-the-badge&labelColor=08080f" alt="Chronacle — TimeBoard"/>
</p>

<h1 align="center">Chronacle — TimeBoard</h1>

<p align="center">
  <em>Every date has a feed. Posts can arrive from any point in time.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/SSE-realtime-22c55e?style=flat-square" alt="SSE Realtime"/>
</p>

---

## The Idea

**Chronacle** is a temporal message board — a place where every date in human history has its own permanent, public feed. You pick a date, write a message, and the system stamps it with *when* you actually wrote it. The gap between the date you're writing *to* and the moment you write *from* becomes the message itself.

- Want to annotate the day you were born? You'll be writing **from the future**.
- Journaling about today? You're writing **in the present**.
- Predicting what tomorrow will bring? You're writing **from the past** — before tomorrow arrives.

A date never closes. It stays open forever, accumulating perspectives from people writing across different moments in time. The result is a layered, temporal record — part diary, part time capsule, part collective memory.

---

## The Inspiration — Stephen Hawking's Party for Time Travelers

<blockquote>
"I sat there a long time, but no one came."<br/>
— <strong>Stephen Hawking</strong>, <em>Into the Universe with Stephen Hawking</em>, 2010
</blockquote>

On **June 28, 2009**, Stephen Hawking hosted a champagne reception at the University of Cambridge. He decorated the hall with balloons and a banner that read *"Welcome, Time Travellers."* He prepared glasses, set up the food, and waited.

**Nobody came.**

And that was entirely the point. Hawking only sent out the invitations ***after*** the party had already ended. The logic was elegant: if backward time travel is ever possible, at least one future traveler would have known about the party and shown up. The empty room was not a failure — it was an experimental result. The silence was data.

### How Chronacle extends the experiment

Chronacle is built on the same foundational logic:

| Hawking's Party | Chronacle |
|---|---|
| The invitation was sent *after* the event | Posts can be written *after* a date has passed |
| Only a time traveler could have attended | The temporal badge reveals *when* you wrote relative to the date |
| The empty room was meaningful data | An empty feed for a date is its own kind of silence |
| The gap between event and invitation was the test | The gap between `for_date` and `written_at` is the record |

Hawking proved that the **absence of evidence is evidence of absence** — at least for his party. Chronacle inverts it: every post is evidence of *presence* — proof that someone, somewhere, at some point in time, thought this date mattered enough to write about.

The infrastructure exists now. If a time traveler ever wants to post a message to June 28, 2009, the feed is already here waiting.

---

## Three Temporal Voices

Every post on Chronacle is automatically classified into one of three temporal perspectives, based on when it was written relative to the date it targets:

| Badge | Voice | Meaning |
|---|---|---|
| 🕰️ **From the Past** | Anticipation | Written *before* the date arrived. You see it coming — hopes, fears, predictions. The weight of the unknown. |
| 📅 **On This Day** | Presence | Written *on* the date itself. No hindsight, no foresight. A pure, unfiltered contemporaneous record. |
| ✨ **From the Future** | Retrospection | Written *after* the date passed. You carry its outcome. Like Hawking looking back at his empty party — the absence now has meaning. |

---

## Architecture & Flowchart

### System Overview

```
┌───────────────────────────────────────────────────────┐
│                     CLIENT (Browser)                  │
│                                                       │
│   ┌─────────────┐    ┌──────────────────────────┐     │
│   │  home.html   │    │      index.html (Board)  │     │
│   │  Landing     │───▶│  Date nav · Post form    │     │
│   │  Page        │    │  Live feed · SSE stream  │     │
│   └─────────────┘    └──────────────────────────┘     │
└────────────────────────────┬──────────────────────────┘
                             │ HTTP / SSE
                             ▼
┌───────────────────────────────────────────────────────┐
│                   FastAPI Server (oracle.py)           │
│                                                       │
│   GET  /          → Landing page (home.html)          │
│   GET  /board     → TimeBoard UI (index.html)         │
│   POST /post      → Create a post for a date          │
│   GET  /feed/{d}  → Fetch all posts for date d        │
│   GET  /stream/{d}→ SSE: real-time post stream        │
│   GET  /dates     → Active dates with post counts     │
│                                                       │
│   ┌───────────────────────────────────────────┐       │
│   │  In-Memory Subscriber Registry            │       │
│   │  date_string → [asyncio.Queue, ...]       │       │
│   │  (powers real-time SSE fan-out)           │       │
│   └───────────────────────────────────────────┘       │
└────────────────────────────┬──────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────┐
│                  SQLite Database (oracle.db)           │
│                                                       │
│   posts                                               │
│   ├── id          INTEGER PRIMARY KEY AUTOINCREMENT   │
│   ├── content     TEXT NOT NULL                        │
│   ├── author      TEXT NOT NULL DEFAULT 'anon'        │
│   ├── for_date    DATE NOT NULL (indexed)             │
│   └── written_at  DATETIME NOT NULL                   │
└───────────────────────────────────────────────────────┘
```

### Request Flow — Posting a Message

```
User writes message          POST /post
for June 28, 2009    ──────────────────────▶  FastAPI
                                                │
                                    ┌───────────┴───────────┐
                                    │ Validate:             │
                                    │  • for_date ≤ today   │
                                    │  • content not empty  │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │ Stamp written_at      │
                                    │ with UTC now          │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │ INSERT into SQLite    │
                                    │ oracle.db → posts     │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │ Fan-out via SSE       │
                                    │ Push to all queues    │
                                    │ subscribed to         │
                                    │ "2009-06-28"          │
                                    └───────────┬───────────┘
                                                │
                                                ▼
                          All connected clients see the post
                          appear instantly with temporal badge:
                          ✨ from the future
                          (written in 2026, for a date in 2009)
```

### Real-Time Streaming (SSE)

```
Client opens /stream/2009-06-28
        │
        ▼
   EventSource connects
        │
        ▼
   Server creates asyncio.Queue
   and registers it under "2009-06-28"
        │
        ├──── waits ────┐
        │               │
        │     Another user posts to 2009-06-28
        │               │
        │     Server pushes post JSON into all
        │     queues registered for that date
        │               │
        ◀───────────────┘
        │
   data: {"id":42,"content":"...","author":"hawking_fan",...}
        │
        ▼
   Client renders post card with temporal badge
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | Async Python web framework with auto-generated OpenAPI docs |
| **Database** | [SQLite](https://sqlite.org/) | Lightweight, zero-config embedded database |
| **Real-time** | Server-Sent Events (SSE) | One-way server→client push for live feed updates |
| **Async I/O** | `asyncio.Queue` | In-memory pub/sub fan-out for SSE subscribers |
| **Frontend** | Vanilla HTML/CSS/JS | No build step, no framework — just the browser |
| **Validation** | [Pydantic](https://docs.pydantic.dev/) | Request body validation and serialization |
| **Server** | [Uvicorn](https://www.uvicorn.org/) | ASGI server for running FastAPI |

---

## Project Structure

```
Chronacle/
├── oracle.py            # Main FastAPI app — TimeBoard server
├── main.py              # Alternate API (async database variant)
├── models.py            # Pydantic models for the alternate API
├── database.py          # Async database layer (databases + aiosqlite)
├── requirements.txt     # Python dependencies
├── static/
│   ├── home.html        # Landing page — concept, Hawking story, how-it-works
│   └── index.html       # TimeBoard — interactive date feed with live SSE
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/DebasishTripathy13/Chronacle.git
cd Chronacle

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
# Start the TimeBoard server
uvicorn oracle:app --reload --port 8000
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

| URL | What you'll see |
|---|---|
| `http://localhost:8000` | Landing page — the concept, Hawking's story, how it works |
| `http://localhost:8000/board` | The TimeBoard — navigate dates, post messages, watch the live feed |
| `http://localhost:8000/docs` | Auto-generated Swagger API docs |

---

## API Reference

### `POST /post`

Create a post targeting a specific date.

```json
{
  "content": "Nobody came to the party.",
  "author": "hawking_fan",
  "for_date": "2009-06-28"
}
```

**Rules:**
- `for_date` must be today or earlier (no future dates)
- `content` is required
- `author` defaults to `"anon"`

**Response** `201`:

```json
{
  "id": 1,
  "content": "Nobody came to the party.",
  "author": "hawking_fan",
  "for_date": "2009-06-28",
  "written_at": "2026-03-02T14:30:00"
}
```

### `GET /feed/{for_date}`

Retrieve all posts for a given date.

```
GET /feed/2009-06-28?limit=50&offset=0
```

### `GET /stream/{for_date}`

Open an SSE connection for real-time updates on a date's feed.

```
GET /stream/2009-06-28
```

Returns `text/event-stream` with `data:` frames as new posts arrive.

### `GET /dates`

List dates that have posts, ordered by most recent, with counts.

```json
[
  { "for_date": "2009-06-28", "count": 5 },
  { "for_date": "2026-03-02", "count": 12 }
]
```

---

## The Philosophy

> The distinction between past, present, and future is only a stubbornly persistent illusion.
> — **Albert Einstein**

Chronacle treats time not as a wall, but as a dimension you can annotate. A date is not something that happens and disappears — it's a coordinate in time that remains permanently addressable. Anyone can leave a mark on it, from any point.

Hawking's empty party proved that **the absence of visitors says something about the nature of time**. Chronacle says: even if no one can travel through time, everyone can *write across it*. And in that writing — in the gap between when you write and the date you write to — there is meaning.

Every post is a small act of temporal empathy: reaching across time to say *this day mattered*.

---

## Future Possibilities

- **Temporal heatmap** — visualize which dates accumulate the most posts across time
- **Anniversary alerts** — get notified when someone posts to a date you've written to
- **Date debates** — see how perspectives on the same date differ based on when they were written
- **Export timeline** — generate a personal timeline from all dates you've annotated
- **Public API keys** — allow third-party apps to write to the TimeBoard

---

## License

This project is open source. Built with curiosity and a quiet respect for the arrow of time.

---

<p align="center">
  <em>Inspired by Stephen Hawking's 2009 party for time travelers.</em><br/>
  <em>He sat there a long time. No one came. The feed is still open.</em>
</p>
