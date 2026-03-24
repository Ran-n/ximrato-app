#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.000000
Revised: 2026/03/24 17:25:27.874296
"""

import asyncio
import base64
import logging
import mimetypes
from datetime import date, datetime
from urllib.parse import urlparse

import flet as ft
import httpx

from ximrato_app.api import users as users_api
from ximrato_app.api.client import get_client
from ximrato_app.api.errors import parse_422

log = logging.getLogger("ximrato_app.screens.profile")

_SEX_OPTIONS = [
    ft.dropdown.Option("", "Prefer not to say"),
    ft.dropdown.Option("male", "Male"),
    ft.dropdown.Option("female", "Female"),
    ft.dropdown.Option("other", "Other"),
]


async def profile_view(page: ft.Page) -> ft.View:
    token = page.session.store.get("access_token")

    # --- Pre-fetch all data before building any widget ---

    def _fetch_initial() -> tuple[dict, dict, str]:
        me = users_api.get_me(token)
        cfg = users_api.get_config(token)
        src = ""
        url = me.get("avatar_url")
        if url:
            try:
                with get_client(token) as c:
                    r = c.get(urlparse(url).path)
                    r.raise_for_status()
                src = base64.b64encode(r.content).decode()
            except Exception:
                pass
        return me, cfg, src

    try:
        me, cfg, initial_b64 = await asyncio.to_thread(_fetch_initial)
    except (httpx.HTTPStatusError, httpx.RequestError):
        me, cfg, initial_b64 = {}, {}, ""

    log.info("profile_view: avatar b64 len=%d", len(initial_b64))

    # --- Initialize state from fetched data ---

    _original: list[dict] = [
        {
            "display_name": me.get("display_name") or "",
            "sex": me.get("sex") or "",
            "date_of_birth": me.get("date_of_birth") or "",
            "height": str(me["height"]) if me.get("height") is not None else "",
        }
    ]
    _avatar_url: list[str | None] = [me.get("avatar_url")]
    dob_str = _original[0]["date_of_birth"]
    _selected_dob: list[date | None] = [
        date.fromisoformat(dob_str) if dob_str else None
    ]
    _pending_avatar: list = [None]
    _date_picker: list[ft.DatePicker | None] = [None]
    _file_picker = ft.FilePicker()

    # --- Build widgets with data already present ---

    _avatar_img = ft.Image(
        src=initial_b64 or "",
        width=96,
        height=96,
        border_radius=ft.BorderRadius.all(48),
        fit=ft.BoxFit.COVER,
        visible=bool(initial_b64),
    )
    avatar_circle = ft.Stack(
        controls=[
            ft.CircleAvatar(
                content=ft.Icon(
                    ft.Icons.PERSON,
                    size=48,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                radius=48,
            ),
            _avatar_img,
        ],
        width=96,
        height=96,
    )
    remove_btn = ft.TextButton("Remove", visible=bool(initial_b64))

    _height_suffix = ft.Text(cfg.get("height_unit", ""))
    display_name = ft.TextField(
        label="Display name",
        hint_text="How you want to be called",
        value=_original[0]["display_name"],
    )
    sex = ft.Dropdown(
        label="Sex", options=_SEX_OPTIONS, value=_original[0]["sex"] or ""
    )
    height = ft.TextField(
        label="Height",
        keyboard_type=ft.KeyboardType.NUMBER,
        suffix=_height_suffix,
        value=_original[0]["height"],
    )
    dob_text = ft.Text(
        _selected_dob[0].strftime("%B %d, %Y") if _selected_dob[0] else "",
        size=14,
        color=ft.Colors.ON_SURFACE_VARIANT,
    )
    dob_button = ft.TextButton(
        "Change date of birth" if _selected_dob[0] else "Set date of birth",
        on_click=lambda _: _pick_date(),
    )
    status = ft.Text(visible=False)
    error = ft.Text("", color=ft.Colors.RED_400, visible=False)

    # --- Helpers ---

    def _show_avatar(src: str | None) -> None:
        _avatar_img.src = src or ""
        _avatar_img.visible = bool(src)
        remove_btn.visible = bool(src)

    def _clear_status() -> None:
        status.visible = False
        error.visible = False

    # --- Avatar actions ---

    async def _pick_avatar(e):
        files = await _file_picker.pick_files(
            allowed_extensions=["jpg", "jpeg", "png", "webp"],
            allow_multiple=False,
            with_data=True,
        )
        if not files:
            return
        f = files[0]
        mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if f.bytes is not None:
            data = bytes(f.bytes)
        elif f.path is not None:
            with open(f.path, "rb") as fh:
                data = fh.read()
        else:
            return
        _pending_avatar[0] = (data, f.name, mime)
        _show_avatar(base64.b64encode(data).decode())
        _clear_status()
        page.update()

    def _on_remove_avatar(e):
        _pending_avatar[0] = ""
        _show_avatar(None)
        _clear_status()
        page.update()

    remove_btn.on_click = _on_remove_avatar

    # --- Date picker ---

    def _pick_date():
        def _on_date_result(e):
            val = e.control.value
            if val:
                _selected_dob[0] = val.date() if isinstance(val, datetime) else val
                dob_text.value = _selected_dob[0].strftime("%B %d, %Y")
                dob_button.text = "Change date of birth"
                _clear_status()
                page.update()

        if _date_picker[0] is None:
            _date_picker[0] = ft.DatePicker(
                first_date=date(1900, 1, 1),
                last_date=date.today(),
                on_change=_on_date_result,
            )
            page.overlay.append(_date_picker[0])

        _date_picker[0].open = True
        page.update()

    # --- Save ---

    def on_save(e):
        _clear_status()
        fields = {}
        original = _original[0]

        if display_name.value.strip() != original.get("display_name", ""):
            fields["display_name"] = display_name.value.strip() or None
        if (sex.value or "") != original.get("sex", ""):
            fields["sex"] = sex.value or None

        dob_val = _selected_dob[0].isoformat() if _selected_dob[0] else ""
        if dob_val != original.get("date_of_birth", ""):
            fields["date_of_birth"] = dob_val or None

        h_val = height.value.strip()
        if h_val != original.get("height", ""):
            if h_val:
                try:
                    fields["height"] = float(h_val)
                except ValueError:
                    error.value = "Height must be a number."
                    error.visible = True
                    page.update()
                    return
            else:
                fields["height"] = None

        pending = _pending_avatar[0]
        if not fields and pending is None:
            return

        try:
            if pending is not None:
                if pending:
                    av_data, av_filename, av_mime = pending
                    users_api.upload_avatar(token, av_data, av_filename, av_mime)
                    _avatar_url[0] = True
                    _show_avatar(base64.b64encode(av_data).decode())
                else:
                    users_api.delete_avatar(token)
                    _avatar_url[0] = None
                    _show_avatar(None)
                _pending_avatar[0] = None
                log.info("avatar %s", "uploaded" if pending else "removed")

            if fields:
                data = users_api.update_me(token, **fields)
                _original[0]["display_name"] = data.get("display_name") or ""
                _original[0]["sex"] = data.get("sex") or ""
                _original[0]["date_of_birth"] = data.get("date_of_birth") or ""
                _original[0]["height"] = (
                    str(data["height"]) if data.get("height") is not None else ""
                )
                display_name.value = _original[0]["display_name"]
                sex.value = _original[0]["sex"] or ""
                height.value = _original[0]["height"]
                log.info("profile updated")

            status.value = "Saved."
            status.color = ft.Colors.GREEN_400
            status.visible = True
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            error.value = (
                "File too large (max 5 MB)."
                if pending and code == 413
                else parse_422(exc.response)
                if code == 422
                else "Something went wrong. Please try again."
            )
            error.visible = True
        except httpx.RequestError:
            error.value = "Could not reach the server."
            error.visible = True
        page.update()

    # --- Wire up ---

    def _on_field_change(e):
        _clear_status()
        page.update()

    for field in (display_name, height):
        field.on_change = _on_field_change
        field.on_submit = on_save
    sex.on_change = _on_field_change

    def _on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/home")

    page.on_keyboard_event = _on_keyboard

    return ft.View(
        route="/profile",
        appbar=ft.AppBar(
            title=ft.Text("Profile"),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/home"),
            ),
            actions=[
                ft.IconButton(
                    ft.Icons.MANAGE_ACCOUNTS,
                    tooltip="Account settings",
                    on_click=lambda _: page.run_task(page.push_route, "/account"),
                ),
                ft.IconButton(
                    ft.Icons.STRAIGHTEN,
                    tooltip="Unit settings",
                    on_click=lambda _: page.run_task(page.push_route, "/settings"),
                ),
            ],
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Column(
                            [
                                avatar_circle,
                                ft.Row(
                                    [
                                        ft.TextButton(
                                            "Change photo",
                                            on_click=_pick_avatar,
                                        ),
                                        remove_btn,
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        display_name,
                        sex,
                        ft.Column(
                            [
                                ft.Text(
                                    "Date of birth",
                                    size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                ft.Row(
                                    [dob_text, dob_button],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=2,
                        ),
                        height,
                        error,
                        status,
                        ft.Button("Save", on_click=on_save, width=float("inf")),
                    ],
                    spacing=16,
                    width=320,
                ),
                padding=ft.Padding.symmetric(horizontal=32, vertical=24),
                alignment=ft.Alignment(0, -0.5),
                expand=True,
            )
        ],
        scroll=ft.ScrollMode.AUTO,
    )
