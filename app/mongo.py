from __future__ import annotations

from pymongo import MongoClient
from pymongo.collection import Collection

from .config import settings

BOT_ID = "default"

_client: MongoClient | None = None


def client() -> MongoClient:
    global _client
    if _client is None:
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL não configurada no .env")
        _client = MongoClient(settings.database_url, serverSelectionTimeoutMS=12000)
    return _client


def database():
    return client().get_default_database()


def col(name: str) -> Collection:
    return database()[name]


def ping() -> None:
    client().admin.command("ping")
