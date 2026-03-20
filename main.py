#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.074618
Revised: 2026/03/20 09:49:19.058972
"""

import logging

import flet as ft

from ximrato_app.screens.home import home_view
from ximrato_app.screens.login import login_view
from ximrato_app.screens.profile import profile_view
from ximrato_app.screens.register import register_view

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
            page.go("/login")
            return

        if route in _PUBLIC and token:
            log.info("authenticated user on %r → redirecting to /home", route)
            page.go("/home")
            return

        page.views.clear()
        if route == "/register":
            page.views.append(register_view(page))
        elif route == "/home":
            page.views.append(home_view(page))
        elif route == "/profile":
            page.views.append(profile_view(page))
        else:
            page.views.append(login_view(page))

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")


ft.run(main)
