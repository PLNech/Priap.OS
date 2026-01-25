"""High-level market helpers that fall back to browser automation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .auth import get_credentials
from .browser import LeekWarsBrowser


def _capture_snapshot(page, snapshot_path: Optional[Path]) -> None:
    """Persist screenshot/HTML to help debug failures."""
    if not snapshot_path or page is None:
        return
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = snapshot_path.with_suffix(".png")
    html_path = snapshot_path.with_suffix(".html")
    try:
        page.screenshot(path=str(png_path))
    except Exception:
        pass
    try:
        html_path.write_text(page.content())
    except Exception:
        pass


def buy_fight_pack_via_browser(
    quantity: int = 1,
    headless: bool = True,
    wait_ms: int = 1500,
    snapshot_path: Optional[Path] = None,
) -> bool:
    """Buy a 50-fight pack through the web UI using Playwright.

    Args:
        quantity: Number of packs to buy (defaults to 1).
        headless: Whether to run the browser in headless mode.
        wait_ms: Delay after confirming purchase to let UI settle.
        snapshot_path: Optional base path for debugging artifacts (.png/.html).

    Returns:
        True if the purchase workflow completed without raising.

    Raises:
        RuntimeError: If login fails or the UI flow is not reachable.
    """
    if quantity < 1:
        raise ValueError("quantity must be >= 1")

    username, password = get_credentials()
    browser = LeekWarsBrowser(headless=headless)
    page = None
    try:
        browser.start()
        if not browser.login(username, password):
            raise RuntimeError("Browser login failed")

        page = browser.page
        browser.goto("/market")
        page.wait_for_selector(".fight-pack", timeout=15000)

        # Fight packs show up as router-links with /market/fight_pack_XX href.
        pack_link = page.locator("a[href='/market/fight_pack_50']").first
        pack_link.wait_for(state="visible", timeout=5000)
        pack_link.click()

        for _ in range(quantity):
            try:
                buy_button = page.locator(".buy-button:not([disabled])").first
                buy_button.wait_for(state="visible", timeout=5000)
            except PlaywrightTimeoutError as exc:
                raise RuntimeError("Buy button did not appear or was disabled") from exc

            buy_button.click()

            try:
                confirm = page.locator(".popup .buy.green").first
                confirm.wait_for(state="visible", timeout=5000)
            except PlaywrightTimeoutError as exc:
                raise RuntimeError("Confirmation popup did not appear") from exc

            confirm.click()
            page.wait_for_timeout(wait_ms)
        return True
    except PlaywrightTimeoutError as exc:
        _capture_snapshot(page, snapshot_path)
        raise RuntimeError(f"Timed out interacting with market UI at {page.url if page else 'unknown page'}") from exc
    except Exception:
        _capture_snapshot(page, snapshot_path)
        raise
    finally:
        browser.close()
