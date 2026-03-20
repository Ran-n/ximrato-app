#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.074618
Revised: 2026/03/20 12:19:12.638367
"""

import logging

import flet as ft

from ximrato_app.screens.account import account_view
from ximrato_app.screens.cardio import cardio_view
from ximrato_app.screens.home import home_view
from ximrato_app.screens.login import login_view
from ximrato_app.screens.metrics import metrics_view
from ximrato_app.screens.profile import profile_view
from ximrato_app.screens.register import register_view
from ximrato_app.screens.session import session_view
from ximrato_app.screens.settings import settings_view

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ximrato_app")

_PUBLIC = {"/login", "/register"}


def main(page: ft.Page):
    page.title = "ximrato"
    page.theme_mode = ft.ThemeMode.DARK

    store = page.session.store

    def route_change(e):
        route = page.route
        token = store.get("access_token")
        log.info("route change: %r authenticated=%s", route, bool(token))

        if route not in _PUBLIC and not token:
            log.info("unauthenticated access to %r → redirecting to /login", route)
            page.run_task(page.push_route, "/login")
            return

        if route in _PUBLIC and token:
            log.info("authenticated user on %r → redirecting to /home", route)
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
        elif route == "/settings":
            page.views.append(settings_view(page))
        elif route == "/session":
            page.views.append(session_view(page))
        elif route == "/cardio":
            page.views.append(cardio_view(page))
        elif route == "/metrics":
            page.views.append(metrics_view(page))
        else:
            page.views.append(login_view(page))

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.run_task(page.push_route, page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.run_task(page.push_route, "/login")


ft.run(main)
