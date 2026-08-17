from datetime import UTC, datetime, timedelta

from ai_marketplace_monitor.activity import ActivityLedger
from ai_marketplace_monitor.facebook import FacebookMarketplace
from ai_marketplace_monitor.monitor import MarketplaceMonitor


def test_completed_search_and_ai_rating_are_added_to_the_durable_activity_ledger(tmp_path, monkeypatch):
    ledger = ActivityLedger(tmp_path / "activity.sqlite3")
    monkeypatch.setattr("ai_marketplace_monitor.facebook.activity", ledger)
    monkeypatch.setattr("ai_marketplace_monitor.monitor.activity", ledger)
    now = datetime.now(UTC)

    FacebookMarketplace._record_search(
        item="cnc", marketplace="facebook", phrase="CNC router", city="Denver", listing_count=2
    )
    MarketplaceMonitor._record_rating(item="cnc", score=5)

    summary = ledger.summary(now - timedelta(minutes=1), now + timedelta(minutes=1))
    assert summary["cnc"] == {"searches": 1, "ratings": {5: 1}}
