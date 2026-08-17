from datetime import UTC, datetime, timedelta

from ai_marketplace_monitor.activity import ActivityLedger


def test_summary_counts_searches_and_ratings_by_item_for_the_requested_window(tmp_path):
    ledger = ActivityLedger(tmp_path / "activity.sqlite3")
    now = datetime(2026, 8, 17, 21, 0, tzinfo=UTC)

    ledger.record_search(
        item="cnc", marketplace="facebook", phrase="CNC router", city="Denver", listing_count=4,
        occurred_at=now - timedelta(hours=2),
    )
    ledger.record_search(
        item="cnc", marketplace="facebook", phrase="CNC machine", city="Denver", listing_count=0,
        occurred_at=now - timedelta(hours=25),
    )
    ledger.record_rating(item="cnc", score=5, occurred_at=now - timedelta(hours=1))
    ledger.record_rating(item="cnc", score=3, occurred_at=now - timedelta(hours=3))
    ledger.record_rating(item="3d_printer", score=4, occurred_at=now - timedelta(hours=4))
    ledger.record_rating(item="3d_printer", score=5, occurred_at=now - timedelta(hours=26))

    summary = ledger.summary(now - timedelta(days=1), now, items=["cnc", "3d_printer", "jointer"])

    assert summary["cnc"] == {"searches": 1, "ratings": {3: 1, 5: 1}}
    assert summary["3d_printer"] == {"searches": 0, "ratings": {4: 1}}
    assert summary["jointer"] == {"searches": 0, "ratings": {}}


def test_summary_includes_an_event_at_the_start_and_excludes_one_at_the_end(tmp_path):
    ledger = ActivityLedger(tmp_path / "activity.sqlite3")
    start = datetime(2026, 8, 16, 21, 0, tzinfo=UTC)
    end = start + timedelta(days=1)

    ledger.record_rating(item="cnc", score=5, occurred_at=start)
    ledger.record_rating(item="cnc", score=4, occurred_at=end)

    assert ledger.summary(start, end)["cnc"]["ratings"] == {5: 1}
