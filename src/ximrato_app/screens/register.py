#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.338934
Revised: 2026/03/27 09:46:28.432393
"""

import flet as ft
import httpx

from ximrato_app.api import auth as auth_api
from ximrato_app.api import users as users_api
from ximrato_app.api.errors import parse_422
from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn


def register_view(page: ft.Page) -> ft.View:
    store = page.session.store
    tr = Translator(store.get("lang") or "en")

    username = ft.TextField(
        label=tr("register.username"),
        autofocus=True,
        value=store.get("__reg_username") or "",
        on_change=lambda e: store.set("__reg_username", e.control.value),
    )
    email = ft.TextField(
        label=tr("register.email"),
        value=store.get("__reg_email") or "",
        on_change=lambda e: store.set("__reg_email", e.control.value),
    )
    password = ft.TextField(
        label=tr("register.password"), password=True, can_reveal_password=True
    )
    password2 = ft.TextField(
        label=tr("register.confirm_password"), password=True, can_reveal_password=True
    )
    error = ft.Text(color=ft.Colors.RED_400, visible=False)

    def on_register(e):
        error.visible = False
        if not username.value or not email.value or not password.value:
            error.value = tr("register.err_fill_all")
            error.visible = True
            page.update()
            return
        if "@" not in email.value or "." not in email.value.split("@")[-1]:
            error.value = tr("register.err_email")
            error.visible = True
            page.update()
            return
        if password.value != password2.value:
            error.value = tr("register.err_passwords")
            error.visible = True
            page.update()
            return
        try:
            data = auth_api.register(
                username.value.strip(), email.value.strip(), password.value
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 409:
                detail = exc.response.json().get("detail", "")
                error.value = (
                    tr("register.err_username_taken")
                    if "username" in detail
                    else tr("register.err_email_taken")
                )
            elif status == 422:
                error.value = parse_422(exc.response)
            else:
                error.value = tr("common.err_generic")
            error.visible = True
            page.update()
            return
        except httpx.RequestError:
            error.value = tr("common.err_server")
            error.visible = True
            page.update()
            return
        pre_reg_lang = store.get("lang")
        store.set("access_token", data["access_token"])
        store.set("refresh_token", data["refresh_token"])
        store.set("__reg_username", None)
        store.set("__reg_email", None)
        try:
            if pre_reg_lang is not None:
                users_api.update_config(data["access_token"], language=pre_reg_lang)
            else:
                cfg = users_api.get_config(data["access_token"])
                store.set("lang", cfg.get("language") or "en")
        except Exception:
            if pre_reg_lang is None:
                store.set("lang", "en")
        page.run_task(page.push_route, "/home")

    username.on_submit = on_register
    email.on_submit = on_register
    password.on_submit = on_register
    password2.on_submit = on_register

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/login")

    page.on_keyboard_event = on_keyboard

    return ft.View(
        route="/register",
        appbar=ft.AppBar(actions=[lang_flag_btn(page)], elevation=0),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Image(src="logo.svg", width=80, height=80),
                        ft.Text(tr("register.heading"), size=14),
                        ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                        username,
                        email,
                        password,
                        password2,
                        error,
                        ft.Button(
                            tr("register.submit"),
                            on_click=on_register,
                            width=float("inf"),
                        ),
                        ft.TextButton(
                            tr("register.to_login"),
                            on_click=lambda _: page.run_task(page.push_route, "/login"),
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
