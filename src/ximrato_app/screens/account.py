#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:04:44.000000
Revised: 2026/03/28 14:34:04.495129
"""

import logging

import flet as ft
import httpx

from ximrato_app.api import auth as auth_api
from ximrato_app.api import users as users_api
from ximrato_app.api.errors import parse_422
from ximrato_app.auth_utils import handle_401, handle_401_sync
from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn

log = logging.getLogger("ximrato_app.screens.account")


def account_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang") or "en")
    token = page.session.store.get("access_token")

    username = ft.TextField(label=tr("account.username"), autofocus=True)
    email = ft.TextField(label=tr("account.email"), keyboard_type=ft.KeyboardType.EMAIL)
    current_password = ft.TextField(
        label=tr("account.current_password"),
        password=True,
        can_reveal_password=True,
    )
    new_password = ft.TextField(
        label=tr("account.new_password"),
        password=True,
        can_reveal_password=True,
    )
    confirm_password = ft.TextField(
        label=tr("account.confirm_password"),
        password=True,
        can_reveal_password=True,
    )

    status = ft.Text(visible=False)
    error = ft.Text(color=ft.Colors.RED_400, visible=False)

    original: dict = {}

    async def load(*, _retried: bool = False) -> None:
        nonlocal token
        try:
            data = users_api.get_me(token)
            original["username"] = data["username"]
            original["email"] = data["email"]
            username.value = data["username"]
            email.value = data["email"]
            log.info("account loaded for user_id=%s", data["id"])
            page.update()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await load(_retried=True)
                return
            error.value = tr("account.err_load")
            error.visible = True
            page.update()
        except httpx.RequestError:
            error.value = tr("common.err_server")
            error.visible = True
            page.update()

    def on_save(e, _retried=False):
        nonlocal token
        error.visible = False
        status.visible = False
        fields = {}

        if username.value.strip() != original.get("username", ""):
            fields["username"] = username.value.strip()
        if email.value.strip() != original.get("email", ""):
            fields["email"] = email.value.strip()

        if new_password.value:
            if not current_password.value:
                error.value = tr("account.err_fill_password")
                error.visible = True
                page.update()
                return
            if new_password.value != confirm_password.value:
                error.value = tr("account.err_passwords")
                error.visible = True
                page.update()
                return
            fields["current_password"] = current_password.value
            fields["password"] = new_password.value

        if not fields:
            return

        try:
            data = users_api.update_me(token, **fields)
            original["username"] = data["username"]
            original["email"] = data["email"]
            username.value = data["username"]
            email.value = data["email"]
            current_password.value = ""
            new_password.value = ""
            confirm_password.value = ""
            status.value = tr("common.saved")
            status.color = ft.Colors.GREEN_400
            status.visible = True
            log.info("account updated for user_id=%s", data["id"])
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code == 401 and not _retried:
                new_tok = handle_401_sync(page)
                if new_tok:
                    token = new_tok
                    on_save(e, _retried=True)
                return
            if code == 400:
                error.value = tr("account.err_wrong_password")
            elif code == 409:
                detail = exc.response.json().get("detail", "")
                error.value = (
                    tr("account.err_username_taken")
                    if "username" in detail
                    else tr("account.err_email_taken")
                )
            elif code == 422:
                error.value = parse_422(exc.response)
            else:
                error.value = tr("common.err_generic")
            error.visible = True
        except httpx.RequestError:
            error.value = tr("common.err_server")
            error.visible = True
        page.update()

    def on_field_change(e):
        status.visible = False
        error.visible = False
        page.update()

    def on_logout(e):
        try:
            auth_api.logout(token)
        except Exception:
            pass
        page.session.store.set("access_token", None)
        page.session.store.set("refresh_token", None)
        page.run_task(page.push_route, "/login")

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/profile")

    for field in (username, email, current_password, new_password, confirm_password):
        field.on_change = on_field_change
        field.on_submit = on_save
    page.on_keyboard_event = on_keyboard

    page.run_task(load)

    return ft.View(
        route="/account",
        appbar=ft.AppBar(
            title=ft.Text(tr("account.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/profile"),
            ),
            actions=[
                lang_flag_btn(page),
                ft.IconButton(
                    ft.Icons.HISTORY,
                    tooltip=tr("account.history_tooltip"),
                    on_click=lambda _: page.run_task(page.push_route, "/auth-history"),
                ),
            ],
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        username,
                        email,
                        ft.Divider(height=8),
                        ft.Text(
                            tr("account.change_password_heading"),
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        current_password,
                        new_password,
                        confirm_password,
                        error,
                        status,
                        ft.Button(
                            tr("common.save"), on_click=on_save, width=float("inf")
                        ),
                        ft.Divider(height=24),
                        ft.Button(
                            tr("common.log_out"),
                            icon=ft.Icons.LOGOUT,
                            on_click=on_logout,
                            width=float("inf"),
                            style=ft.ButtonStyle(
                                color=ft.Colors.ERROR,
                            ),
                        ),
                    ],
                    spacing=12,
                    width=320,
                ),
                padding=ft.padding.symmetric(horizontal=32, vertical=24),
                alignment=ft.Alignment(0, -0.5),
                expand=True,
            )
        ],
        scroll=ft.ScrollMode.AUTO,
    )
