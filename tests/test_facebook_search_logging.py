from unittest.mock import Mock

from ai_marketplace_monitor.facebook import FacebookMarketplace
from ai_marketplace_monitor.marketplace import Listing


def test_logs_search_failure_only_when_result_parser_returns_no_listings() -> None:
    logger = Mock()
    listing = Listing(
        marketplace="facebook",
        name="",
        id="123",
        title="3D printer",
        image="",
        price="$100",
        post_url="https://www.facebook.com/marketplace/item/123/",
        location="Denver, CO",
        seller="",
        condition="",
        description="",
    )

    FacebookMarketplace._log_search_outcome(logger, "3D printer", "denver", [listing])

    logger.error.assert_not_called()

    FacebookMarketplace._log_search_outcome(logger, "3D printer", "denver", [])

    logger.error.assert_called_once()
    assert "Failed to get search results" in logger.error.call_args.args[0]


def test_saves_browser_session_only_after_search_returns_listings() -> None:
    marketplace = Mock(spec=FacebookMarketplace)
    marketplace.save_session_state = Mock()
    listing = Listing(
        marketplace="facebook",
        name="",
        id="123",
        title="3D printer",
        image="",
        price="$100",
        post_url="https://www.facebook.com/marketplace/item/123/",
        location="Denver, CO",
        seller="",
        condition="",
        description="",
    )

    FacebookMarketplace._save_session_after_search(marketplace, [])
    marketplace.save_session_state.assert_not_called()

    FacebookMarketplace._save_session_after_search(marketplace, [listing])
    marketplace.save_session_state.assert_called_once_with()
