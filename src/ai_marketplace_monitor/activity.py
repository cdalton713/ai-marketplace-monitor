"""Durable, queryable evidence of Marketplace monitor activity.

The normal monitor log is optimized for troubleshooting and rotates frequently.
This ledger retains compact, timestamped search and AI-rating events so a daily
recap can prove actual work across container restarts without storing listing
contents or notification secrets.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


class ActivityLedger:
    """Append monitor activity and summarize a time window from a SQLite file."""

    retention_days = 90

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_events (
                    occurred_at REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    item TEXT NOT NULL,
                    marketplace TEXT,
                    score INTEGER,
                    phrase TEXT,
                    city TEXT,
                    listing_count INTEGER
                )
                """
            )
            db.execute(
                """
                CREATE INDEX IF NOT EXISTS activity_events_window
                ON activity_events (occurred_at, event_type, item)
                """
            )

    @staticmethod
    def _timestamp(occurred_at: datetime | None) -> float:
        if occurred_at is None:
            occurred_at = datetime.now(UTC)
        if occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        return occurred_at.timestamp()

    def _record(self, event_type: str, item: str, occurred_at: datetime | None = None, **fields: Any) -> None:
        timestamp = self._timestamp(occurred_at)
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO activity_events
                  (occurred_at, event_type, item, marketplace, score, phrase, city, listing_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    event_type,
                    item,
                    fields.get("marketplace"),
                    fields.get("score"),
                    fields.get("phrase"),
                    fields.get("city"),
                    fields.get("listing_count"),
                ),
            )
            db.execute(
                "DELETE FROM activity_events WHERE occurred_at < ?",
                (timestamp - self.retention_days * 24 * 60 * 60,),
            )

    def record_search(
        self,
        *,
        item: str,
        marketplace: str,
        phrase: str,
        city: str,
        listing_count: int,
        occurred_at: datetime | None = None,
    ) -> None:
        """Record one completed Marketplace query, including zero-result scans."""
        self._record(
            "search",
            item,
            occurred_at,
            marketplace=marketplace,
            phrase=phrase,
            city=city,
            listing_count=listing_count,
        )

    def record_rating(
        self, *, item: str, score: int, occurred_at: datetime | None = None
    ) -> None:
        """Record an AI score for one evaluated listing."""
        self._record("rating", item, occurred_at, score=score)

    def summary(
        self, start: datetime, end: datetime, items: Iterable[str] = ()
    ) -> dict[str, dict[str, Any]]:
        """Return per-item searches and rating counts in [start, end)."""
        start_ts = self._timestamp(start)
        end_ts = self._timestamp(end)
        if end_ts < start_ts:
            raise ValueError("end must not precede start")

        result: dict[str, dict[str, Any]] = {
            item: {"searches": 0, "ratings": {}} for item in items
        }
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT event_type, item, score, COUNT(*)
                FROM activity_events
                WHERE occurred_at >= ? AND occurred_at < ?
                GROUP BY event_type, item, score
                """,
                (start_ts, end_ts),
            ).fetchall()
        ratings: dict[str, dict[int, int]] = defaultdict(dict)
        for event_type, item, score, count in rows:
            result.setdefault(item, {"searches": 0, "ratings": {}})
            if event_type == "search":
                result[item]["searches"] += count
            elif event_type == "rating" and score is not None:
                ratings[item][int(score)] = count
        for item, per_score in ratings.items():
            result[item]["ratings"] = dict(sorted(per_score.items()))
        return result


def format_daily_recap(summary: dict[str, dict[str, Any]], hours: int = 24) -> str:
    """Render compact, human-readable proof of search and scoring activity."""
    total_searches = sum(int(data["searches"]) for data in summary.values())
    lines = [
        f"Marketplace daily recap — last {hours} hours",
        f"Searches completed: {total_searches}",
    ]
    for item, data in summary.items():
        searches = int(data["searches"])
        search_word = "search" if searches == 1 else "searches"
        ratings = data["ratings"]
        rating_text = (
            ", ".join(f"{score}★={count}" for score, count in ratings.items())
            if ratings
            else "none"
        )
        lines.append(f"{item.capitalize()}: {searches} {search_word}; ratings {rating_text}")
    return "\n".join(lines)
