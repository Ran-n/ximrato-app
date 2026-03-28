#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:04:44.000000
Revised: 2026/03/28 14:34:04.377481
"""

import logging

import flet as ft
import httpx

from ximrato_app.api import users as users_api
from ximrato_app.auth_utils import handle_401, handle_401_sync
from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn

log = logging.getLogger("ximrato_app.screens.settings")


def settings_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang") or "en")
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

    title_text = ft.Text(tr("settings.title"))
    status = ft.Text(visible=False)
    error = ft.Text(color=ft.Colors.RED_400, visible=False)
    save_btn = ft.Button(tr("common.save"), on_click=None, width=float("inf"))

    original: dict = {}

    async def load_config(*, _retried: bool = False) -> None:
        nonlocal token
        try:
            data = users_api.get_config(token)
            original["weight_unit"] = data["weight_unit"]
            original["distance_unit"] = data["distance_unit"]
            original["height_unit"] = data["height_unit"]
            weight_unit.value = data["weight_unit"]
            distance_unit.value = data["distance_unit"]
            height_unit.value = data["height_unit"]
            log.info("config loaded")
            page.update()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await load_config(_retried=True)
                return
            error.value = tr("settings.err_load")
            error.visible = True
            page.update()
        except httpx.RequestError:
            error.value = tr("common.err_server")
            error.visible = True
            page.update()

    def on_save(e, _retried=False):
        nonlocal token
        cur_tr = Translator(page.session.store.get("lang") or "en")
        error.visible = False
        status.visible = False
        fields = {}
        if weight_unit.value != original.get("weight_unit"):
            fields["weight_unit"] = weight_unit.value
        if distance_unit.value != original.get("distance_unit"):
            fields["distance_unit"] = distance_unit.value
        if height_unit.value != original.get("height_unit"):
            fields["height_unit"] = height_unit.value
        if not fields:
            return
        try:
            data = users_api.update_config(token, **fields)
            original["weight_unit"] = data["weight_unit"]
            original["distance_unit"] = data["distance_unit"]
            original["height_unit"] = data["height_unit"]
            weight_unit.value = data["weight_unit"]
            distance_unit.value = data["distance_unit"]
            height_unit.value = data["height_unit"]
            status.value = cur_tr("settings.saved")
            status.color = ft.Colors.GREEN_400
            status.visible = True
            log.info("config updated")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_tok = handle_401_sync(page)
                if new_tok:
                    token = new_tok
                    on_save(e, _retried=True)
                return
            error.value = cur_tr("common.err_generic")
            error.visible = True
        except httpx.RequestError:
            error.value = cur_tr("common.err_server")
            error.visible = True
        page.update()

    def on_change(e):
        status.visible = False
        error.visible = False
        page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/profile")

    save_btn.on_click = on_save
    weight_unit.on_change = on_change
    distance_unit.on_change = on_change
    height_unit.on_change = on_change
    page.on_keyboard_event = on_keyboard

    page.run_task(load_config)

    return ft.View(
        route="/settings",
        appbar=ft.AppBar(
            title=title_text,
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/profile"),
            ),
            actions=[lang_flag_btn(page)],
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        weight_unit,
                        distance_unit,
                        height_unit,
                        error,
                        status,
                        save_btn,
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
