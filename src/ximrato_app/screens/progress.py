#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/31 19:59:24.991798
Revised: 2026/04/07 13:15:38.216748
"""

import logging

import flet as ft
import flet.canvas as cv
import httpx

from ximrato_app.api import metrics as metrics_api
from ximrato_app.api import sessions as sessions_api
from ximrato_app.api.sessions import localized_exercise_name
from ximrato_app.auth_utils import handle_401
from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn

log = logging.getLogger("ximrato_app.screens.progress")

_BODY_METRICS = ["weight", "waist", "chest", "hips", "neck", "arms", "thighs"]


def _adapt_body_entries(entries: list[dict], metric_type: str) -> list[dict]:
    """Filter body metric entries by type, sort by date, and adapt for charting."""
    filtered = sorted(
        [e for e in entries if e["metric_type"] == metric_type],
        key=lambda x: x["logged_at"],
    )
    return [{"date": e["logged_at"][:10], "max_weight": e["value"]} for e in filtered]


def progress_view(page: ft.Page) -> ft.View:
    lang = page.session.store.get("lang") or "en"
    tr = Translator(lang)
    token: str = page.session.store.get("access_token")

    # ── restore saved state ────────────────────────────────────────────────────
    _saved_tab: int = page.session.store.get("progress_tab") or 0
    _saved_exercise: str | None = page.session.store.get("progress_exercise_id")
    _saved_metric: str | None = page.session.store.get("progress_metric")

    # ── state ──────────────────────────────────────────────────────────────────
    _exercises: list[dict] = []
    _body_data: list[dict] = []

    # ── shared controls ────────────────────────────────────────────────────────
    error_text = ft.Text("", color=ft.Colors.ERROR, size=13)

    # ── dropdowns (never moved — always live in their fixed Row) ───────────────
    strength_exercise_dd = ft.Dropdown(
        label=tr("progress.select_exercise"),
        expand=True,
    )
    body_metric_dd = ft.Dropdown(
        label=tr("progress.select_metric"),
        expand=True,
        value=_saved_metric,
        options=[
            ft.dropdown.Option("weight", tr("metrics.weight_label")),
            *[ft.dropdown.Option(m, tr(f"metrics.{m}").split(" (")[0]) for m in _BODY_METRICS if m != "weight"],
        ],
    )

    # Fixed Rows — each dropdown lives here permanently, rows are never recreated.
    # dd_area.content swaps between these two rows on tab change (dd_area is always
    # in the initial tree, so this nested swap is reliable).
    _strength_dd_row = ft.Row([strength_exercise_dd], expand=True)
    _body_dd_row = ft.Row([body_metric_dd], expand=True)

    # ── chart builder ──────────────────────────────────────────────────────────
    _CHART_H = 280
    _PAD_L = 52
    _PAD_R = 16
    _PAD_T = 24
    _PAD_B = 40

    def _build_chart(data: list[dict], y_key: str) -> ft.Control:
        if not data:
            return ft.Text(tr("progress.no_data"), italic=True, size=13)

        chart_w = max(int(page.width or 900) - 48, 400)
        values = [float(e[y_key]) for e in data]
        min_v, max_v = min(values), max(values)
        v_range = max(max_v - min_v, 1.0)
        n = len(data)
        draw_w = chart_w - _PAD_L - _PAD_R
        draw_h = _CHART_H - _PAD_T - _PAD_B

        def _x(i: int) -> float:
            return _PAD_L + (i / max(n - 1, 1)) * draw_w

        def _y(v: float) -> float:
            return _PAD_T + (1 - (v - min_v) / v_range) * draw_h

        line_paint = ft.Paint(color=ft.Colors.PRIMARY, stroke_width=2, style=ft.PaintingStyle.STROKE)
        dot_paint = ft.Paint(color=ft.Colors.PRIMARY, style=ft.PaintingStyle.FILL)
        grid_paint = ft.Paint(color=ft.Colors.OUTLINE, stroke_width=1, style=ft.PaintingStyle.STROKE)
        label_style = ft.TextStyle(size=10, color=ft.Colors.ON_SURFACE_VARIANT)
        value_style = ft.TextStyle(size=10, color=ft.Colors.ON_SURFACE)

        shapes: list = []

        # horizontal grid lines + y-axis labels (min / mid / max)
        for frac in [0.0, 0.5, 1.0]:
            yl = _PAD_T + (1 - frac) * draw_h
            y_val = min_v + frac * v_range
            shapes.append(cv.Line(_PAD_L, yl, chart_w - _PAD_R, yl, paint=grid_paint))
            shapes.append(cv.Text(0, yl - 7, value=f"{y_val:.1f}", style=label_style))

        # data line segments
        for i in range(n - 1):
            shapes.append(cv.Line(_x(i), _y(values[i]), _x(i + 1), _y(values[i + 1]), paint=line_paint))

        # dots + value/date labels (skip some when dense)
        label_every = max(1, n // 12)
        for i, (entry, v) in enumerate(zip(data, values, strict=True)):
            cx, cy = _x(i), _y(v)
            shapes.append(cv.Circle(cx, cy, 4, paint=dot_paint))
            if i % label_every == 0:
                shapes.append(cv.Text(cx - 10, cy - 18, value=f"{v:.1f}", style=value_style))
                shapes.append(cv.Text(cx - 10, _CHART_H - _PAD_B + 8, value=entry["date"][-5:], style=label_style))

        return cv.Canvas(shapes=shapes, width=chart_w, height=_CHART_H)

    # ── strength callbacks ─────────────────────────────────────────────────────
    async def _on_strength_exercise_change(e):
        if not strength_exercise_dd.value:
            return
        page.session.store.set("progress_exercise_id", strength_exercise_dd.value)
        await _load_strength_chart(int(strength_exercise_dd.value))

    strength_exercise_dd.on_select = _on_strength_exercise_change

    async def _load_strength_chart(exercise_id: int, *, _retried: bool = False) -> None:
        nonlocal token
        # Swap chart area directly — active_panel is always in the initial tree,
        # so this nested-content swap is reliable.
        active_panel.content = ft.ProgressRing()
        page.update()
        try:
            data = sessions_api.get_exercise_progress(token, exercise_id)
            active_panel.content = _build_chart(data, "max_weight")
            page.update()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _load_strength_chart(exercise_id, _retried=True)
                return
            active_panel.content = ft.Text(
                tr("common.err_status", code=exc.response.status_code), color=ft.Colors.ERROR, size=13
            )
            page.update()
        except httpx.RequestError:
            active_panel.content = ft.Text(tr("common.err_server"), color=ft.Colors.ERROR, size=13)
            page.update()

    # ── body metric callbacks ──────────────────────────────────────────────────
    async def _on_body_metric_change(e):
        metric = body_metric_dd.value
        if not metric:
            return
        page.session.store.set("progress_metric", metric)
        await _load_body_chart(metric)

    body_metric_dd.on_select = _on_body_metric_change

    async def _load_body_chart(metric_type: str) -> None:
        active_panel.content = ft.ProgressRing()
        page.update()
        try:
            adapted = _adapt_body_entries(_body_data, metric_type)
            active_panel.content = _build_chart(adapted, "max_weight")
            page.update()
        except Exception as exc:
            log.exception("body chart render error")
            active_panel.content = ft.Text(str(exc), color=ft.Colors.ERROR, size=13)
            page.update()

    # ── layout ─────────────────────────────────────────────────────────────────
    # dd_area is always in the initial tree; its content swaps between
    # _strength_dd_row and _body_dd_row on tab change — reliable nested swap.
    dd_area = ft.Container(
        content=_strength_dd_row if _saved_tab == 0 else _body_dd_row,
        padding=ft.Padding.symmetric(horizontal=16),
    )

    _placeholder_key = "progress.select_exercise" if _saved_tab == 0 else "progress.select_metric"
    # active_panel holds only the chart; it is always in the initial tree.
    active_panel = ft.Container(
        content=ft.Text(tr(_placeholder_key), italic=True, size=13),
        padding=ft.Padding.only(top=16),
        expand=True,
    )

    _tab_labels = [tr("progress.tab_strength"), tr("progress.tab_body")]
    _tab_idx: list[int] = [_saved_tab]
    _tab_btns: list[ft.TextButton] = []

    def _switch_tab(idx: int) -> None:
        _tab_idx[0] = idx
        page.session.store.set("progress_tab", idx)
        for i, btn in enumerate(_tab_btns):
            btn.style = ft.ButtonStyle(color=ft.Colors.PRIMARY if i == idx else ft.Colors.ON_SURFACE_VARIANT)
        dd_area.content = _strength_dd_row if idx == 0 else _body_dd_row
        active_panel.content = ft.Text(
            tr("progress.select_exercise" if idx == 0 else "progress.select_metric"), italic=True, size=13
        )
        page.update()
        if idx == 1 and body_metric_dd.value:
            page.run_task(_load_body_chart, body_metric_dd.value)
        elif idx == 0 and strength_exercise_dd.value:
            page.run_task(_load_strength_chart, int(strength_exercise_dd.value))

    for _i, _lbl in enumerate(_tab_labels):
        _tab_btns.append(
            ft.TextButton(
                content=_lbl,
                on_click=lambda e, i=_i: _switch_tab(i),
                style=ft.ButtonStyle(color=ft.Colors.PRIMARY if _i == _saved_tab else ft.Colors.ON_SURFACE_VARIANT),
            )
        )

    tab_bar = ft.Row(_tab_btns, spacing=0)
    layout = ft.Column(
        [
            tab_bar,
            ft.Divider(height=1),
            ft.Container(error_text, padding=ft.Padding.symmetric(horizontal=16)),
            ft.Container(dd_area, padding=ft.Padding.only(top=16)),
            active_panel,
        ],
        expand=True,
        spacing=0,
    )

    # ── async init ─────────────────────────────────────────────────────────────
    async def _do_init(*, _retried: bool = False) -> None:
        nonlocal _exercises, _body_data, token
        try:
            _exercises = sessions_api.list_exercises(token)
            _body_data = metrics_api.list_body_metrics(token)
            strength_exercise_dd.options = [
                ft.dropdown.Option(str(ex["id"]), localized_exercise_name(ex, lang)) for ex in _exercises
            ]
            if _saved_exercise and any(str(ex["id"]) == _saved_exercise for ex in _exercises):
                strength_exercise_dd.value = _saved_exercise
            page.update()
            if body_metric_dd.value:
                await _load_body_chart(body_metric_dd.value)
            if strength_exercise_dd.value:
                await _load_strength_chart(int(strength_exercise_dd.value))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _do_init(_retried=True)
                return
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            page.update()
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            page.update()
        except Exception as exc:
            log.exception("_do_init unexpected error")
            error_text.value = str(exc)
            page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/home")

    page.on_keyboard_event = on_keyboard
    page.run_task(_do_init)

    return ft.View(
        route="/progress",
        appbar=ft.AppBar(
            title=ft.Text(tr("progress.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/home"),
            ),
            actions=[lang_flag_btn(page)],
        ),
        controls=[layout],
    )
