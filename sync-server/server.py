"""Lightweight sync server for Islamic PWA cross-device data synchronization.

Stores key-value pairs with timestamps in SQLite.
Last-write-wins strategy per key.
"""

import sqlite3
import time
from contextlib import contextmanager
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import AUTH_TOKEN, CORS_ORIGINS, DB_PATH

app = FastAPI(title="Islamic PWA Sync", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "PUT", "OPTIONS"],
    allow_headers=["*"],
)


# --- Database ---


def init_db():
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_data (
                key       TEXT PRIMARY KEY,
                value     TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# --- Auth ---


def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if token != AUTH_TOKEN:
        raise HTTPException(403, "Invalid token")


# --- Models ---


class SyncItem(BaseModel):
    key: str
    value: str
    updated_at: float


class PutSyncRequest(BaseModel):
    items: List[SyncItem]


class SyncResponse(BaseModel):
    key: str
    value: str
    updated_at: float


# --- Endpoints ---


@app.get("/api/health")
def health():
    return {"status": "ok", "time": time.time()}


@app.get("/api/sync", response_model=List[SyncResponse])
def get_all(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    with get_db() as db:
        rows = db.execute("SELECT key, value, updated_at FROM sync_data").fetchall()
    return [dict(r) for r in rows]


@app.get("/api/sync/{key}", response_model=SyncResponse)
def get_key(key: str, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    with get_db() as db:
        row = db.execute(
            "SELECT key, value, updated_at FROM sync_data WHERE key = ?", (key,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Key not found")
    return dict(row)


@app.put("/api/sync")
def put_sync(body: PutSyncRequest, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    updated = 0
    with get_db() as db:
        for item in body.items:
            existing = db.execute(
                "SELECT updated_at FROM sync_data WHERE key = ?", (item.key,)
            ).fetchone()
            # Only write if incoming is newer (or key doesn't exist)
            if not existing or item.updated_at >= existing["updated_at"]:
                db.execute(
                    """
                    INSERT INTO sync_data (key, value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = excluded.updated_at
                    """,
                    (item.key, item.value, item.updated_at),
                )
                updated += 1
    return {"updated": updated, "total": len(body.items)}


# --- Startup ---


@app.on_event("startup")
def on_startup():
    init_db()


if __name__ == "__main__":
    import uvicorn

    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8420)
