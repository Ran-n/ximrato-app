#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.000000
Revised: 2026/03/20 09:53:36.177084
"""

import logging

import flet as ft
import httpx

from ximrato_app.api import users as users_api

log = logging.getLogger("ximrato_app.screens.profile")


def profile_view(page: ft.Page) -> ft.View:
    token = page.session.store.get("access_token")

    username = ft.TextField(label="Username")
    email = ft.TextField(label="Email")
    password = ft.TextField(
        label="New password (leave blank to keep)",
        password=True,
        can_reveal_password=True,
    )
    status = ft.Text(visible=False)
    error = ft.Text(color=ft.Colors.RED_400, visible=False)

    original: dict = {}

    def load_profile():
        try:
            data = users_api.get_me(token)
            original["username"] = data["username"]
            original["email"] = data["email"]
            username.value = data["username"]
            email.value = data["email"]
            log.info("profile loaded for user_id=%s", data["id"])
            page.update()
        except httpx.RequestError:
            error.value = "Could not reach the server."
            error.visible = True
            page.update()

    def on_save(e):
        error.visible = False
        status.visible = False
        fields = {}
        if username.value.strip() != original.get("username", ""):
            fields["username"] = username.value.strip()
        if email.value.strip() != original.get("email", ""):
            fields["email"] = email.value.strip()
        if password.value:
            fields["password"] = password.value
        if not fields:
            return
        try:
            data = users_api.update_me(token, **fields)
            original["username"] = data["username"]
            original["email"] = data["email"]
            username.value = data["username"]
            email.value = data["email"]
            password.value = ""
            status.value = "Profile updated."
            status.color = ft.Colors.GREEN_400
            status.visible = True
            log.info("profile updated for user_id=%s", data["id"])
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code == 409:
                detail = exc.response.json().get("detail", "")
                error.value = (
                    "Username already taken."
                    if "username" in detail
                    else "Email already registered."
                )
            elif code == 422:
                detail = exc.response.json().get("detail", [])
                if isinstance(detail, list) and detail:
                    loc = " → ".join(
                        str(p) for p in detail[0].get("loc", []) if p != "body"
                    )
                    msg = detail[0].get("msg", "invalid input")
                    error.value = f"{loc}: {msg}" if loc else msg
                else:
                    error.value = "Invalid input."
            else:
                error.value = f"Server error ({code})."
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
            page.go("/home")

    username.on_change = on_field_change
    email.on_change = on_field_change
    password.on_change = on_field_change
    username.on_submit = on_save
    email.on_submit = on_save
    password.on_submit = on_save
    page.on_keyboard_event = on_keyboard

    load_profile()

    return ft.View(
        route="/profile",
        appbar=ft.AppBar(
            title=ft.Text("Profile"),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.go("/home"),
            ),
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        username,
                        email,
                        password,
                        error,
                        status,
                        ft.ElevatedButton("Save", on_click=on_save, width=float("inf")),
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
