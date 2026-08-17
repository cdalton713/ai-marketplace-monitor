from unittest.mock import MagicMock

from ai_marketplace_monitor.facebook import FacebookMarketplace, FacebookMarketplaceConfig


def configured_marketplace() -> FacebookMarketplace:
    marketplace = FacebookMarketplace(name="facebook", browser=MagicMock())
    marketplace.configure(FacebookMarketplaceConfig(name="facebook"))
    return marketplace


def test_create_page_restores_saved_browser_session(tmp_path) -> None:
    marketplace = configured_marketplace()
    state_file = tmp_path / "facebook-storage-state.json"
    state_file.write_text('{"cookies": [], "origins": []}', encoding="utf-8")
    marketplace.session_state_path = state_file

    marketplace.create_page()

    marketplace.browser.new_context.assert_called_once_with(
        proxy=None, storage_state=str(state_file)
    )


def test_save_session_state_persists_current_browser_context(tmp_path) -> None:
    marketplace = configured_marketplace()
    state_file = tmp_path / "facebook-storage-state.json"
    marketplace.session_state_path = state_file
    marketplace.create_page()
    marketplace.page.context.storage_state.side_effect = lambda path: state_file.write_text(
        '{"cookies": [], "origins": []}', encoding="utf-8"
    )

    marketplace.save_session_state()

    marketplace.page.context.storage_state.assert_called_once_with(path=str(state_file))
