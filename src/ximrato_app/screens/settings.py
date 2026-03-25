#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:04:44.000000
Revised: 2026/03/25 12:30:45.799469
"""

import logging

import flet as ft
import httpx

from ximrato_app.api import users as users_api
from ximrato_app.i18n import Translator

log = logging.getLogger("ximrato_app.screens.settings")


def settings_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang", "en"))
    token = page.session.store.get("access_token")

    weight_unit = ft.Dropdown(
        label=tr("settings.weight_unit"),
        options=[
            ft.dropdown.Option("kg", "kg"),
            ft.dropdown.Option("lb", "lb"),
        ],
    )
    distance_unit = ft.Dropdown(
        label=tr("settings.distance_unit"),
        options=[
            ft.dropdown.Option("km", "km"),
            ft.dropdown.Option("mi", "mi"),
        ],
    )
    height_unit = ft.Dropdown(
        label=tr("settings.height_unit"),
        options=[
            ft.dropdown.Option("cm", "cm"),
            ft.dropdown.Option("in", "in"),
        ],
    )
    language_dd = ft.Dropdown(
        label=tr("settings.language"),
        options=[
            ft.dropdown.Option("en", tr("settings.lang_en")),
            ft.dropdown.Option("gl", tr("settings.lang_gl")),
        ],
    )

    status = ft.Text(visible=False)
    error = ft.Text(color=ft.Colors.RED_400, visible=False)

    original: dict = {}

    def load_config():
        try:
            data = users_api.get_config(token)
            original["weight_unit"] = data["weight_unit"]
            original["distance_unit"] = data["distance_unit"]
            original["height_unit"] = data["height_unit"]
            original["language"] = data["language"]
            weight_unit.value = data["weight_unit"]
            distance_unit.value = data["distance_unit"]
            height_unit.value = data["height_unit"]
            language_dd.value = data["language"]
            log.info("config loaded")
            page.update()
        except httpx.HTTPStatusError:
            error.value = tr("settings.err_load")
            error.visible = True
            page.update()
        except httpx.RequestError:
            error.value = tr("common.err_server")
            error.visible = True
            page.update()

    def on_save(e):
        error.visible = False
        status.visible = False
        fields = {}
        if weight_unit.value != original.get("weight_unit"):
            fields["weight_unit"] = weight_unit.value
        if distance_unit.value != original.get("distance_unit"):
            fields["distance_unit"] = distance_unit.value
        if height_unit.value != original.get("height_unit"):
            fields["height_unit"] = height_unit.value
        if language_dd.value != original.get("language"):
            fields["language"] = language_dd.value
        if not fields:
            return
        try:
            data = users_api.update_config(token, **fields)
            original["weight_unit"] = data["weight_unit"]
            original["distance_unit"] = data["distance_unit"]
            original["height_unit"] = data["height_unit"]
            original["language"] = data["language"]
            weight_unit.value = data["weight_unit"]
            distance_unit.value = data["distance_unit"]
            height_unit.value = data["height_unit"]
            language_dd.value = data["language"]
            page.session.store.set("lang", data["language"])
            status.value = tr("settings.saved")
            status.color = ft.Colors.GREEN_400
            status.visible = True
            log.info("config updated")
        except httpx.HTTPStatusError:
            error.value = tr("common.err_generic")
            error.visible = True
        except httpx.RequestError:
            error.value = tr("common.err_server")
            error.visible = True
        page.update()

    def on_change(e):
        status.visible = False
        error.visible = False
        page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/profile")

    weight_unit.on_change = on_change
    distance_unit.on_change = on_change
    height_unit.on_change = on_change
    language_dd.on_change = on_change
    page.on_keyboard_event = on_keyboard

    load_config()

    return ft.View(
        route="/settings",
        appbar=ft.AppBar(
            title=ft.Text(tr("settings.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/profile"),
            ),
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        weight_unit,
                        distance_unit,
                        height_unit,
                        language_dd,
                        error,
                        status,
                        ft.Button(
                            tr("common.save"), on_click=on_save, width=float("inf")
                        ),
                    ],
                    spacing=12,
                    width=320,
                ),
                padding=32,
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
