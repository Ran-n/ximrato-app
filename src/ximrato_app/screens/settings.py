#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:04:44.000000
Revised: 2026/03/20 11:51:17.780179
"""

import logging

import flet as ft
import httpx

from ximrato_app.api import users as users_api

log = logging.getLogger("ximrato_app.screens.settings")


def settings_view(page: ft.Page) -> ft.View:
    token = page.session.store.get("access_token")

    weight_unit = ft.Dropdown(
        label="Weight unit",
        options=[
            ft.dropdown.Option("kg", "kg"),
            ft.dropdown.Option("lb", "lb"),
        ],
    )
    distance_unit = ft.Dropdown(
        label="Distance unit",
        options=[
            ft.dropdown.Option("km", "km"),
            ft.dropdown.Option("mi", "mi"),
        ],
    )
    height_unit = ft.Dropdown(
        label="Height unit",
        options=[
            ft.dropdown.Option("cm", "cm"),
            ft.dropdown.Option("in", "in"),
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
            weight_unit.value = data["weight_unit"]
            distance_unit.value = data["distance_unit"]
            height_unit.value = data["height_unit"]
            log.info("config loaded")
            page.update()
        except httpx.RequestError:
            error.value = "Could not reach the server."
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
            status.value = "Settings saved."
            status.color = ft.Colors.GREEN_400
            status.visible = True
            log.info("config updated")
        except httpx.HTTPStatusError:
            error.value = "Something went wrong. Please try again."
            error.visible = True
        except httpx.RequestError:
            error.value = "Could not reach the server."
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
    page.on_keyboard_event = on_keyboard

    load_config()

    return ft.View(
        route="/settings",
        appbar=ft.AppBar(
            title=ft.Text("Unit Settings"),
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
                        error,
                        status,
                        ft.Button("Save", on_click=on_save, width=float("inf")),
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
