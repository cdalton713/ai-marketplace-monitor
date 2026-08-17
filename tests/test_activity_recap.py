from ai_marketplace_monitor.activity import format_daily_recap


def test_format_daily_recap_is_a_compact_high_level_proof_with_zeroes_and_rating_counts():
    message = format_daily_recap(
        {
            "cnc": {"searches": 4, "ratings": {3: 2, 5: 1}},
            "jointer": {"searches": 1, "ratings": {}},
        },
        hours=24,
    )

    assert "Marketplace daily recap — last 24 hours" in message
    assert "Searches completed: 5" in message
    assert "Cnc: 4 searches; ratings 3★=2, 5★=1" in message
    assert "Jointer: 1 search; ratings none" in message
