#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.000000
Revised: 2026/03/24 07:36:02.620338
"""

import base64
import logging
import mimetypes
import time
from datetime import date, datetime

import flet as ft
import httpx

from ximrato_app.api import users as users_api
from ximrato_app.api.errors import parse_422

log = logging.getLogger("ximrato_app.screens.profile")

_SEX_OPTIONS = [
    ft.dropdown.Option("", "Prefer not to say"),
    ft.dropdown.Option("male", "Male"),
    ft.dropdown.Option("female", "Female"),
    ft.dropdown.Option("other", "Other"),
]


def profile_view(page: ft.Page) -> ft.View:
    token = page.session.store.get("access_token")

    display_name = ft.TextField(
        label="Display name", hint_text="How you want to be called"
    )
    sex = ft.Dropdown(label="Sex", options=_SEX_OPTIONS)
    height = ft.TextField(
        label="Height",
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    dob_text = ft.Text(size=14, color=ft.Colors.ON_SURFACE_VARIANT)
    dob_button = ft.TextButton("Set date of birth", on_click=lambda _: pick_date())

    status = ft.Text(visible=False)
    error = ft.Text(color=ft.Colors.RED_400, visible=False)

    original: dict = {}
    selected_dob: date | None = None
    _date_picker: ft.DatePicker | None = None
    _avatar_url: list[str | None] = [None]
    # non-empty str = path to upload, "" = remove, None = no change
    _pending_avatar: list[str | None] = [None]

    _file_picker = ft.FilePicker()

    avatar_img = ft.Image(
        src="",
        width=96,
        height=96,
        fit="cover",
        visible=False,
    )
    avatar_icon = ft.Icon(
        ft.Icons.PERSON,
        size=48,
        color=ft.Colors.ON_SURFACE_VARIANT,
    )
    avatar_circle = ft.Container(
        width=96,
        height=96,
        border_radius=48,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        alignment=ft.Alignment(0, 0),
        content=ft.Stack([avatar_img, avatar_icon]),
    )
    remove_btn = ft.TextButton("Remove", visible=False)

    def _refresh_avatar():
        url = _avatar_url[0]
        if url:
            avatar_img.src = f"{url}?v={int(time.time())}"
            avatar_img.visible = True
            avatar_icon.visible = False
            remove_btn.visible = True
        else:
            avatar_img.visible = False
            avatar_icon.visible = True
            remove_btn.visible = False
        page.update()

    async def _pick_avatar(e):
        files = await _file_picker.pick_files(
            allowed_extensions=["jpg", "jpeg", "png", "webp"],
            allow_multiple=False,
        )
        if not files:
            return
        f = files[0]
        mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if f.path is not None:
            with open(f.path, "rb") as fh:
                data = fh.read()
            preview_src = f.path
        else:
            data = bytes(f.bytes)
            preview_src = f"data:{mime};base64,{base64.b64encode(data).decode()}"
        _pending_avatar[0] = (data, f.name, mime)
        avatar_img.src = preview_src
        avatar_img.visible = True
        avatar_icon.visible = False
        remove_btn.visible = True
        on_field_change(None)

    def on_remove_avatar(e):
        _pending_avatar[0] = ""
        avatar_img.visible = False
        avatar_icon.visible = True
        remove_btn.visible = False
        on_field_change(None)

    remove_btn.on_click = on_remove_avatar

    def pick_date():
        nonlocal _date_picker

        def on_result(e):
            nonlocal selected_dob
            val = e.control.value
            if val:
                selected_dob = val.date() if isinstance(val, datetime) else val
                dob_text.value = selected_dob.strftime("%B %d, %Y")
                dob_button.text = "Change date of birth"
                on_field_change(None)
                page.update()

        if _date_picker is None:
            _date_picker = ft.DatePicker(
                first_date=date(1900, 1, 1),
                last_date=date.today(),
                on_change=on_result,
            )
            page.overlay.append(_date_picker)

        _date_picker.open = True
        page.update()

    def load_profile():
        nonlocal selected_dob
        try:
            data = users_api.get_me(token)
            cfg = users_api.get_config(token)
            original["display_name"] = data.get("display_name") or ""
            original["sex"] = data.get("sex") or ""
            original["date_of_birth"] = data.get("date_of_birth") or ""
            original["height"] = (
                str(data["height"]) if data.get("height") is not None else ""
            )

            display_name.value = original["display_name"]
            sex.value = original["sex"] or ""
            height.value = original["height"]
            height.suffix = ft.Text(cfg["height_unit"])

            dob_raw = original["date_of_birth"]
            if dob_raw:
                selected_dob = date.fromisoformat(dob_raw)
                dob_text.value = selected_dob.strftime("%B %d, %Y")
                dob_button.text = "Change date of birth"
            else:
                selected_dob = None
                dob_text.value = ""
                dob_button.text = "Set date of birth"

            _avatar_url[0] = data.get("avatar_url")
            _refresh_avatar()

            log.info("profile loaded for user_id=%s", data["id"])
        except httpx.HTTPStatusError:
            error.value = "Could not load profile data."
            error.visible = True
            page.update()
        except httpx.RequestError:
            error.value = "Could not reach the server."
            error.visible = True
            page.update()

    def on_save(e):
        nonlocal selected_dob
        error.visible = False
        status.visible = False
        fields = {}

        if display_name.value.strip() != original.get("display_name", ""):
            fields["display_name"] = display_name.value.strip() or None
        if (sex.value or "") != original.get("sex", ""):
            fields["sex"] = sex.value or None

        dob_val = selected_dob.isoformat() if selected_dob else ""
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
                    data_av = users_api.get_me(token)
                    _avatar_url[0] = data_av.get("avatar_url")
                else:
                    users_api.delete_avatar(token)
                    _avatar_url[0] = None
                _pending_avatar[0] = None
                _refresh_avatar()
                log.info("avatar %s", "uploaded" if pending else "removed")

            if fields:
                data = users_api.update_me(token, **fields)
                original["display_name"] = data.get("display_name") or ""
                original["sex"] = data.get("sex") or ""
                original["date_of_birth"] = data.get("date_of_birth") or ""
                original["height"] = (
                    str(data["height"]) if data.get("height") is not None else ""
                )
                display_name.value = original["display_name"]
                sex.value = original["sex"] or ""
                height.value = original["height"]
                log.info("profile updated for user_id=%s", data["id"])

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

    def on_field_change(e):
        status.visible = False
        error.visible = False
        page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/home")

    for field in (display_name, height):
        field.on_change = on_field_change
        field.on_submit = on_save
    sex.on_change = on_field_change
    page.on_keyboard_event = on_keyboard

    load_profile()

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
