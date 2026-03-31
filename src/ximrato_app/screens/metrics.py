#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 12:15:00.000000
Revised: 2026/03/28 14:46:26.346360
"""

import asyncio
import logging
from datetime import datetime

import flet as ft
import httpx

from ximrato_app.api import metrics as metrics_api
from ximrato_app.api import users as users_api
from ximrato_app.auth_utils import handle_401
from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn

log = logging.getLogger("ximrato_app.screens.metrics")

_METRIC_ORDER = ["weight", "waist", "chest", "hips", "neck", "arms", "thighs"]


def _fmt_date(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.strftime("%b %d, %Y  %H:%M")


def _delta_label(latest: float, prev: float) -> str:
    """Format the change from prev to latest as an arrow + signed value."""
    delta = latest - prev
    if delta > 0:
        return f"\u2191 +{delta:g}"
    if delta < 0:
        return f"\u2193 {delta:g}"
    return "\u2192 \u00b10"


def metrics_view(page: ft.Page) -> ft.View:
    tr = Translator(page.session.store.get("lang") or "en")
    token: str = page.session.store.get("access_token")

    # -- state ------------------------------------------------------------------
    past_entries: list[dict] = []
    weight_unit = "kg"

    # -- shared controls --------------------------------------------------------
    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
    error_text = ft.Text("", color=ft.Colors.ERROR, size=13)

    # -- form controls ----------------------------------------------------------
    weight_field = ft.TextField(
        keyboard_type=ft.KeyboardType.NUMBER,
        width=130,
    )
    waist_field = ft.TextField(
        label=tr("metrics.waist"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=130,
    )
    chest_field = ft.TextField(
        label=tr("metrics.chest"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=130,
    )
    hips_field = ft.TextField(
        label=tr("metrics.hips"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=130,
    )
    neck_field = ft.TextField(
        label=tr("metrics.neck"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=130,
    )
    arms_field = ft.TextField(
        label=tr("metrics.arms"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=130,
    )
    thighs_field = ft.TextField(
        label=tr("metrics.thighs"),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=130,
    )

    _field_map = {
        "weight": weight_field,
        "waist": waist_field,
        "chest": chest_field,
        "hips": hips_field,
        "neck": neck_field,
        "arms": arms_field,
        "thighs": thighs_field,
    }

    # -- history helpers --------------------------------------------------------
    def _unit_for(metric_type: str) -> str:
        return weight_unit if metric_type == "weight" else "cm"

    def _type_label(metric_type: str) -> str:
        if metric_type == "weight":
            return tr("metrics.weight_label")
        return tr(f"metrics.{metric_type}").split("(")[0].rstrip()

    def _type_tile(metric_type: str, entries: list[dict]) -> ft.ExpansionTile:
        """Build a per-type history tile. entries are desc-sorted (newest first)."""
        unit = _unit_for(metric_type)
        label = _type_label(metric_type)
        n = len(entries)
        latest_val = f"{entries[0]['value']:g} {unit}"
        entry_word = tr("metrics.entry_one") if n == 1 else tr("metrics.entry_many")
        count_str = f"{n} {entry_word}"

        if n >= 2:
            delta_str = _delta_label(entries[0]["value"], entries[1]["value"])
            subtitle = f"{delta_str}  \u00b7  {count_str}"
        else:
            subtitle = count_str

        tile_controls = [
            ft.ListTile(
                title=ft.Text(f"{e['value']:g} {unit}"),
                subtitle=ft.Text(_fmt_date(e["logged_at"]), size=12),
                dense=True,
                content_padding=ft.Padding.symmetric(horizontal=16, vertical=0),
            )
            for e in entries
        ]

        return ft.ExpansionTile(
            title=ft.Text(f"{label} \u2014 {latest_val}"),
            subtitle=ft.Text(subtitle, size=12),
            controls=tile_controls,
        )

    # -- render -----------------------------------------------------------------
    def _render(clear_error: bool = True) -> None:
        if clear_error:
            error_text.value = ""
        weight_field.label = tr("metrics.weight", unit=weight_unit)

        history: list = []
        if past_entries:
            by_type: dict[str, list[dict]] = {}
            for e in past_entries:
                by_type.setdefault(e["metric_type"], []).append(e)

            history.append(
                ft.Container(
                    ft.Text(tr("metrics.past"), size=13, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.only(left=16, top=8, bottom=4),
                )
            )
            for mt in _METRIC_ORDER:
                if mt in by_type:
                    history.append(_type_tile(mt, by_type[mt]))

        body.controls = [
            ft.Container(
                ft.Column(
                    [
                        ft.Container(
                            ft.Column(
                                [
                                    ft.Row([weight_field], spacing=8),
                                    ft.Row([waist_field, chest_field], spacing=8),
                                    ft.Row([hips_field, neck_field], spacing=8),
                                    ft.Row([arms_field, thighs_field], spacing=8),
                                ],
                                spacing=8,
                            ),
                            padding=ft.Padding.symmetric(horizontal=16),
                        ),
                        ft.Container(
                            error_text,
                            padding=ft.Padding.symmetric(horizontal=16),
                        ),
                        ft.Container(
                            ft.Button(
                                tr("metrics.log"),
                                icon=ft.Icons.CHECK,
                                on_click=lambda _: page.run_task(_do_log),
                                width=float("inf"),
                            ),
                            padding=ft.Padding.symmetric(horizontal=16),
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.padding.only(top=16, bottom=16),
            ),
            ft.Divider(),
            *history,
        ]
        page.update()

    # -- helpers ----------------------------------------------------------------
    def _parse_field(field: ft.TextField, key: str) -> tuple[float | None, str | None]:
        raw = (field.value or "").strip()
        if not raw:
            return None, None
        try:
            value = float(raw)
        except ValueError:
            return None, tr(f"metrics.err_{key}")
        return value, None

    # -- async actions ----------------------------------------------------------
    async def _load(*, _retried: bool = False) -> None:
        nonlocal past_entries, weight_unit, token
        try:
            cfg = await asyncio.to_thread(users_api.get_config, token)
            weight_unit = cfg.get("weight_unit", "kg")
            past_entries = await asyncio.to_thread(metrics_api.list_body_metrics, token)
            _render()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _load(_retried=True)
                return
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            page.update()
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            page.update()

    async def _do_log(*, _retried: bool = False) -> None:
        nonlocal past_entries, token
        error_text.value = ""

        parsed: dict[str, float | None] = {}
        for key, field in _field_map.items():
            value, err = _parse_field(field, key)
            if err:
                error_text.value = err
                _render(clear_error=False)
                return
            parsed[key] = value

        to_log = [(k, v) for k, v in parsed.items() if v is not None]
        if not to_log:
            error_text.value = tr("metrics.err_fill_one")
            _render(clear_error=False)
            return

        try:
            for metric_type, value in to_log:
                await asyncio.to_thread(metrics_api.create_body_metric, token, metric_type, value)
            for field in _field_map.values():
                field.value = ""
            past_entries = await asyncio.to_thread(metrics_api.list_body_metrics, token)
            _render()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _do_log(_retried=True)
                return
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            _render(clear_error=False)
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            _render(clear_error=False)

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/home")

    page.on_keyboard_event = on_keyboard
    page.run_task(_load)

    return ft.View(
        route="/metrics",
        appbar=ft.AppBar(
            title=ft.Text(tr("metrics.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/home"),
            ),
            actions=[lang_flag_btn(page)],
        ),
        controls=[body],
    )
