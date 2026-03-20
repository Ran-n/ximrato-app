#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:41:15.000000
Revised: 2026/03/20 17:06:44.348237
"""

# GUI smoke tests — requires both services running (see conftest.py).
# Run with: uv run pytest tests/test_gui.py
#
# Flet renders via Flutter/Skia canvas. Key Playwright patterns:
#   - Enable accessibility once on first load:
#       flt-semantics-placeholder.dispatch_event("click")
#   - Text fields: get_by_role("textbox", name=..., exact=True).click() + .type()
#   - Labeled buttons: get_by_role("button", name=...)
#   - Icon-only buttons: get_by_role("button").nth(N) — order matches AppBar order
#   - Status/error text: locator("flt-semantics").inner_text() contains the text
#   - Each test logs in independently (no cross-test session state)
#
# Icon button order (no visible label in accessibility tree):
#   Home:    btn[0]=Profile, btn[1]=Log out
#   Profile: btn[0]=back, btn[1]=Account settings, btn[2]=Unit settings
#   Account: btn[0]=back
#   Settings: btn[0]=back, btn[1]=weight dropdown, btn[2]=distance, btn[3]=height
#   Session: btn[0]=back
#     end session → locator("flt-semantics[aria-label='End session']")
#     Flutter tooltip wraps the button in a Semantics node with aria-label but no
#     role; get_by_role("button", name=...) cannot find it — use CSS locator.

import pytest

pytestmark = pytest.mark.gui


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _enable_a11y(page):
    """Enable Flutter accessibility tree. Call once per context on first load."""
    placeholder = page.locator("flt-semantics-placeholder")
    if placeholder.count():
        placeholder.dispatch_event("click")
        page.wait_for_timeout(1500)


def _type(page, label: str, value: str):
    """Click a textbox and type into it (fill() doesn't commit to Flet state)."""
    field = page.get_by_role("textbox", name=label, exact=True)
    field.click()
    field.type(value)


def _click(page, text: str):
    page.get_by_role("button", name=text).click()


def _wait_url(page, path: str, timeout=10000):
    page.wait_for_url(f"**{path}", timeout=timeout)


def _has_text(page, text: str) -> bool:
    """Check if any flt-semantics element contains the given text."""
    for el in page.locator("flt-semantics").all():
        try:
            if text in el.inner_text(timeout=300):
                return True
        except Exception:
            pass
    return False


def _login(page, app_url, username, password):
    """Log in and land on /home."""
    page.goto(app_url)
    _wait_url(page, "/login")
    _enable_a11y(page)
    page.wait_for_timeout(500)
    _type(page, "Username", username)
    _type(page, "Password", password)
    _click(page, "Log in")
    _wait_url(page, "/home")
    page.wait_for_timeout(500)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_register_and_auto_login(page, app_url, gui_credentials):
    page.goto(app_url)
    _wait_url(page, "/login")
    _enable_a11y(page)
    _click(page, "Don't have an account? Register")
    _wait_url(page, "/register")
    page.wait_for_timeout(500)

    # register a one-off account distinct from the shared gui_credentials account
    import time

    user = f"reg{int(time.time())}"
    _type(page, "Username", user)
    _type(page, "Email", f"{user}@example.com")
    _type(page, "Password", "regpass1")
    _type(page, "Confirm password", "regpass1")
    _click(page, "Register")
    _wait_url(page, "/home")

    assert "/home" in page.url


def test_logout_and_login(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])

    page.get_by_role("button").nth(1).click()  # Log out icon
    _wait_url(page, "/login")
    page.wait_for_timeout(500)

    _type(page, "Username", gui_credentials["username"])
    _type(page, "Password", gui_credentials["password"])
    _click(page, "Log in")
    _wait_url(page, "/home")


def test_login_wrong_password(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])

    page.get_by_role("button").nth(1).click()  # Log out icon
    _wait_url(page, "/login")
    page.wait_for_timeout(500)

    _type(page, "Username", gui_credentials["username"])
    _type(page, "Password", "wrongpass")
    _click(page, "Log in")
    page.wait_for_timeout(2000)

    assert _has_text(page, "Wrong username or password")


def test_navigate_to_profile(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])

    page.get_by_role("button").nth(0).click()  # Profile icon
    _wait_url(page, "/profile")


def test_profile_save_display_name(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(0).click()  # Profile icon
    _wait_url(page, "/profile")
    page.wait_for_timeout(500)

    _type(page, "Display name", "Test User")
    _click(page, "Save")
    page.wait_for_timeout(2000)

    assert _has_text(page, "Saved.")


def test_navigate_to_account(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(0).click()  # Profile icon
    _wait_url(page, "/profile")
    page.wait_for_timeout(500)

    page.get_by_role("button").nth(1).click()  # Account settings icon
    _wait_url(page, "/account")


def test_account_wrong_current_password(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(0).click()  # Profile icon
    _wait_url(page, "/profile")
    page.wait_for_timeout(500)
    page.get_by_role("button").nth(1).click()  # Account settings icon
    _wait_url(page, "/account")
    page.wait_for_timeout(500)

    _type(page, "Current password", "wrongpass")
    _type(page, "New password", "newpass1")
    _type(page, "Confirm new password", "newpass1")
    _click(page, "Save")
    page.wait_for_timeout(2000)

    assert _has_text(page, "Current password is incorrect")


def test_navigate_to_settings(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(0).click()  # Profile icon
    _wait_url(page, "/profile")
    page.wait_for_timeout(500)

    page.get_by_role("button").nth(2).click()  # Unit settings icon
    _wait_url(page, "/settings")


def test_settings_change_weight_unit(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(0).click()  # Profile icon
    _wait_url(page, "/profile")
    page.wait_for_timeout(500)
    page.get_by_role("button").nth(2).click()  # Unit settings icon
    _wait_url(page, "/settings")
    page.wait_for_timeout(500)

    # appbar btn[0]=back; dropdowns btn[1]=weight, btn[2]=distance, btn[3]=height
    page.get_by_role("button").nth(1).click()
    page.wait_for_timeout(500)
    _click(page, "lb")
    page.wait_for_timeout(300)
    _click(page, "Save")
    page.wait_for_timeout(2000)

    assert _has_text(page, "Settings saved.")


def test_navigate_to_session(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    _click(page, "Session")
    _wait_url(page, "/session")


def test_session_start_and_end(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    _click(page, "Session")
    _wait_url(page, "/session")
    page.wait_for_timeout(1500)

    _end_session = page.locator(
        "flt-semantics[aria-label='End session'] flt-semantics[role='button']"
    )

    # If a previous run left an active session, end it first so we start clean.
    if not _has_text(page, "Start session"):
        _end_session.click()
        page.wait_for_timeout(3000)

    _click(page, "Start session")
    page.wait_for_timeout(2000)

    _end_session.click()
    page.wait_for_timeout(3000)

    assert _has_text(page, "Start session")


def test_unauthenticated_redirect(page, app_url):
    # navigate first so sessionStorage is accessible, then clear auth state
    page.goto(app_url)
    _enable_a11y(page)
    page.context.clear_cookies()
    page.evaluate("sessionStorage.clear()")
    page.goto(f"{app_url}/#/home")
    _wait_url(page, "/login")
