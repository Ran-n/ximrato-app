#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:41:15.000000
Revised: 2026/03/27 19:28:37.169090
"""

# GUI smoke tests — requires both services running (see conftest.py).
# Run with: uv run pytest tests/test_gui.py
#
# Flet renders via Flutter/Skia canvas. Key Playwright patterns:
#   - Enable accessibility once on first load:
#       flt-semantics-placeholder.dispatch_event("click")
#   - Text fields: .click(click_count=3) to select-all, then .type() to replace
#   - Text buttons (ft.Button / ft.TextButton with visible text): _click(page, "<text>")
#   - Icon buttons (ft.IconButton): tooltip name does NOT map to Playwright accessible
#     name — use get_by_role("button").nth(N) instead.
#   - Flutter accessibility button order: AppBar always comes before body buttons.
#       No leading  → AppBar actions first (0, 1, …), then body buttons
#       With leading → leading (0), AppBar actions (1, 2, …), then body buttons
#   - Per-screen button indices:
#       Home (no leading): 0=lang, 1=Profile, 2=Log out
#         body: Session, Cardio, Body metrics
#       Profile (back=0):  1=lang, 2=account, 3=unit;
#         body: Change photo, [Remove], sex-dd, dob, save  (Remove only when avatar set)
#       Settings (back=0): 1=lang; body: 2=weight-dd, 3=dist-dd, 4=height-dd
#       Session active (back=0): 1=lang, 2=end; body: exercise-dd, rpe-dd, add-set
#   - Avatar: FilePicker opens a native OS dialog — cannot be driven by Playwright.
#     Only button visibility can be tested.
#   - Status/error text: locator("flt-semantics").inner_text() contains the text
#   - Each test logs in independently (no cross-test session state)

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
    """Select-all and replace via typing (fill() doesn't commit to Flet state)."""
    field = page.get_by_role("textbox", name=label, exact=True)
    field.click(click_count=3)
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


def test_navigate_to_cardio(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    _click(page, "Cardio")
    _wait_url(page, "/cardio")


def test_navigate_to_metrics(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    _click(page, "Body metrics")
    _wait_url(page, "/metrics")


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

    page.get_by_role("button").nth(
        2
    ).click()  # Log out (home: no leading → actions first)
    _wait_url(page, "/login")
    page.wait_for_timeout(500)

    _type(page, "Username", gui_credentials["username"])
    _type(page, "Password", gui_credentials["password"])
    _click(page, "Log in")
    _wait_url(page, "/home")


def test_login_wrong_password(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])

    page.get_by_role("button").nth(2).click()  # Log out
    _wait_url(page, "/login")
    page.wait_for_timeout(500)

    _type(page, "Username", gui_credentials["username"])
    _type(page, "Password", "wrongpass")
    _click(page, "Log in")
    page.wait_for_timeout(3000)

    assert _has_text(page, "Wrong username or password")


def test_navigate_to_profile(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])

    page.get_by_role("button").nth(
        1
    ).click()  # Profile (home: no leading → actions first)
    _wait_url(page, "/profile")


def test_profile_save_display_name(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(1).click()  # Profile
    _wait_url(page, "/profile")
    page.wait_for_timeout(2000)

    _type(page, "Display name", "Test User")
    _click(page, "Save")
    page.wait_for_timeout(3000)

    assert _has_text(page, "Saved.")


def test_navigate_to_account(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(1).click()  # Profile
    _wait_url(page, "/profile")
    page.wait_for_timeout(2000)

    page.get_by_role("button").nth(
        2
    ).click()  # Account (first AppBar action after back+lang)
    _wait_url(page, "/account")


def test_account_wrong_current_password(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(1).click()  # Profile
    _wait_url(page, "/profile")
    page.wait_for_timeout(2000)
    page.get_by_role("button").nth(
        2
    ).click()  # Account (first AppBar action after back+lang)
    _wait_url(page, "/account")
    page.wait_for_timeout(1000)

    _type(page, "Current password", "wrongpass")
    _type(page, "New password", "newpass1")
    _type(page, "Confirm new password", "newpass1")
    _click(page, "Save")
    page.wait_for_timeout(3000)

    assert _has_text(page, "Current password is incorrect")


def test_navigate_to_settings(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(1).click()  # Profile
    _wait_url(page, "/profile")
    page.wait_for_timeout(2000)

    page.get_by_role("button").nth(
        3
    ).click()  # Unit (second AppBar action after back+lang)
    _wait_url(page, "/settings")


def test_settings_change_weight_unit(page, app_url, gui_credentials):
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(1).click()  # Profile
    _wait_url(page, "/profile")
    page.wait_for_timeout(2000)
    page.get_by_role("button").nth(
        3
    ).click()  # Unit (second AppBar action after back+lang)
    _wait_url(page, "/settings")
    page.wait_for_timeout(1000)

    # appbar: btn[0]=back, btn[1]=lang
    # dropdowns: btn[2]=weight, btn[3]=distance, btn[4]=height
    page.get_by_role("button").nth(2).click()
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

    # Poll until _load() renders either idle ("Start session") or active ("Exercise").
    for _ in range(20):
        if _has_text(page, "Start session") or _has_text(page, "Exercise"):
            break
        page.wait_for_timeout(500)

    # End session btn is btn[2] — second AppBar action after back + lang flag.
    def _click_end_session():
        page.get_by_role("button").nth(2).click()

    # If a previous run left an active session, end it first so we start clean.
    if not _has_text(page, "Start session"):
        _click_end_session()
        page.wait_for_timeout(3000)

    _click(page, "Start session")
    page.wait_for_timeout(3000)  # wait for _do_start() and _render_active()

    _click_end_session()
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


def test_profile_change_photo_button_visible(page, app_url, gui_credentials):
    # FilePicker is a native OS dialog and cannot be driven by Playwright;
    # only verify the button renders and is accessible.
    _login(page, app_url, gui_credentials["username"], gui_credentials["password"])
    page.get_by_role("button").nth(1).click()  # Profile (AppBar action 1, after lang)
    _wait_url(page, "/profile")
    page.wait_for_timeout(2000)

    assert _has_text(page, "Change photo")
