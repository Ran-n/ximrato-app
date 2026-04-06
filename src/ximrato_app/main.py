#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/24 08:51:53.915049
Revised: 2026/04/05 18:59:23.200289
"""

import asyncio
import logging
import pathlib

import flet as ft

from ximrato_app.screens.account import account_view
from ximrato_app.screens.auth_history import auth_history_view
from ximrato_app.screens.cardio import cardio_view
from ximrato_app.screens.cardio_history import cardio_history_view
from ximrato_app.screens.home import home_view
from ximrato_app.screens.login import login_view
from ximrato_app.screens.metrics import metrics_view
from ximrato_app.screens.profile import profile_view
from ximrato_app.screens.progress import progress_view
from ximrato_app.screens.register import register_view
from ximrato_app.screens.session import session_view
from ximrato_app.screens.session_history import session_history_view
from ximrato_app.screens.settings import settings_view

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    encoding="utf-8",
)
log = logging.getLogger("ximrato_app")

_PUBLIC = {"/login", "/register"}


async def main(page: ft.Page):
    page.title = "ximrato"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.icon = str(pathlib.Path(__file__).parents[2] / "assets" / "icon.ico")

    store = page.session.store

    prefs = ft.SharedPreferences()
    store.set("__prefs", prefs)

    async def route_change(e):
        route = page.route
        token = store.get("access_token")
        log.info("route change: %r authenticated=%s", route, bool(token))

        if route not in _PUBLIC and not token:
            log.info("unauthenticated access to %r -> redirecting to /login", route)
            page.run_task(page.push_route, "/login")
            return

        if route in _PUBLIC and token:
            log.info("authenticated user on %r -> redirecting to /home", route)
            page.run_task(page.push_route, "/home")
            return

        page.views.clear()
        if route == "/register":
            page.views.append(register_view(page))
        elif route == "/home":
            page.views.append(home_view(page))
        elif route == "/profile":
            page.views.append(profile_view(page))
        elif route == "/account":
            page.views.append(account_view(page))
        elif route == "/auth-history":
            page.views.append(auth_history_view(page))
        elif route == "/settings":
            page.views.append(settings_view(page))
        elif route == "/session":
            page.views.append(session_view(page))
        elif route == "/session-history":
            page.views.append(session_history_view(page))
        elif route == "/cardio":
            page.views.append(cardio_view(page))
        elif route == "/cardio-history":
            page.views.append(cardio_history_view(page))
        elif route == "/metrics":
            page.views.append(metrics_view(page))
        elif route == "/progress":
            page.views.append(progress_view(page))
        else:
            page.views.append(login_view(page))

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.run_task(page.push_route, page.views[-1].route)

    async def _init():
        page.views.clear()
        page.views.append(
            ft.View(
                route="/",
                controls=[
                    ft.Container(
                        content=ft.Image(src="logo.svg", width=96, height=96),
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                    )
                ],
            )
        )
        page.update()
        await asyncio.sleep(0)  # yield so send loop flushes patch to Flutter first

        try:
            saved_lang = await prefs.get("lang")
        except Exception:
            log.warning("SharedPreferences.get('lang') timed out — falling back to default lang")
            saved_lang = None
        if saved_lang:
            store.set("lang", saved_lang)
            store.set("__lang_explicit", True)
        await route_change(None)

    store.set("__rebuild", route_change)
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    await _init()
