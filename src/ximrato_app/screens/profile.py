#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.000000
Revised: 2026/03/20 12:10:04.098709
"""

import logging
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
            config = users_api.get_config(token)
            original["display_name"] = data.get("display_name") or ""
            original["sex"] = data.get("sex") or ""
            original["date_of_birth"] = data.get("date_of_birth") or ""
            original["height"] = (
                str(data["height"]) if data.get("height") is not None else ""
            )

            display_name.value = original["display_name"]
            sex.value = original["sex"] or ""
            height.value = original["height"]
            height.suffix = ft.Text(config["height_unit"])

            dob_raw = original["date_of_birth"]
            if dob_raw:
                selected_dob = date.fromisoformat(dob_raw)
                dob_text.value = selected_dob.strftime("%B %d, %Y")
                dob_button.text = "Change date of birth"
            else:
                selected_dob = None
                dob_text.value = ""
                dob_button.text = "Set date of birth"

            log.info("profile loaded for user_id=%s", data["id"])
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

        if not fields:
            return

        try:
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
            status.value = "Saved."
            status.color = ft.Colors.GREEN_400
            status.visible = True
            log.info("profile updated for user_id=%s", data["id"])
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            error.value = (
                parse_422(exc.response)
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
                padding=ft.padding.symmetric(horizontal=32, vertical=24),
                alignment=ft.Alignment(0, -0.5),
                expand=True,
            )
        ],
        scroll=ft.ScrollMode.AUTO,
    )
