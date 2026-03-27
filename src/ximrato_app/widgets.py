#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/25 12:43:14.000000
Revised: 2026/03/27 09:59:00.627404
"""

import flet as ft

_LANG_NAMES = [("en", "English"), ("gl", "Galego"), ("es", "Español")]


def lang_flag_btn(page: ft.Page) -> ft.Container:
    """Flag dropdown to pick a language; rebuilds the current view."""
    current = page.session.store.get("lang") or "en"

    def _on_select(lang: str):
        async def _handler(e):
            page.session.store.set("lang", lang)
            page.session.store.set("__lang_explicit", True)
            prefs = page.session.store.get("__prefs")
            if prefs:
                await prefs.set("lang", lang)
            rebuild = page.session.store.get("__rebuild")
            if rebuild:
                await rebuild(None)

        return _handler

    return ft.Container(
        content=ft.PopupMenuButton(
            content=ft.Image(src=f"flags/{current}.svg", width=24, height=16),
            tooltip="Switch language",
            padding=ft.Padding.symmetric(horizontal=8, vertical=12),
            menu_position=ft.PopupMenuPosition.UNDER,
            popup_animation_style=ft.AnimationStyle(duration=0),
            items=[
                ft.PopupMenuItem(
                    content=ft.Row(
                        [
                            ft.Image(src=f"flags/{lang}.svg", width=24, height=16),
                            ft.Text(name),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    on_click=_on_select(lang),
                )
                for lang, name in _LANG_NAMES
            ],
        ),
        margin=ft.Margin(left=0, top=0, right=16, bottom=0),
    )
