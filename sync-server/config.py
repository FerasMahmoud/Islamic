"""Sync server configuration."""
import os

AUTH_TOKEN = os.environ.get(
    "SYNC_AUTH_TOKEN",
    "3PD7DVOzuhYG4wtr1LKQYIsBfYs6KR-rmD76ukIvuGw",
)

PORT = int(os.environ.get("SYNC_PORT", "8420"))

CORS_ORIGINS = [
    "https://ferasmahmoud.github.io",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
]

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync.db")
