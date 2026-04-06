#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 12:15:00.000000
Revised: 2026/04/06 10:02:15.291219
"""

import logging
from datetime import datetime, timezone

import flet as ft
import httpx

from ximrato_app.api import sessions as sessions_api
from ximrato_app.api import users as users_api
from ximrato_app.api.sessions import localized_exercise_name
from ximrato_app.auth_utils import handle_401
from ximrato_app.i18n import Translator
from ximrato_app.widgets import lang_flag_btn

log = logging.getLogger("ximrato_app.screens.session")

RPE_LABELS: dict[str, str] = {
    "no_reps_left": "No reps left",
    "could_do_1": "Could do 1 more",
    "could_do_2": "Could do 2 more",
    "could_do_3": "Could do 3 more",
    "could_do_4_5": "Could do 4\u20135 more",
    "very_light": "Very light",
}


def _set_label(
    s: dict,
    *,
    rpe_labels: dict[str, str] = RPE_LABELS,
    bw_abbrev: str = "BW",
    rpe_prefix: str = "RPE",
    to_failure_suffix: str = "  \u2713 to failure",
) -> str:
    w = s["weight"]
    weight_str = bw_abbrev if w == 0 else f"{w:g}"
    rpe_str = f"  {rpe_prefix}: {rpe_labels[s['rpe']]}" if s["rpe"] else ""
    failure_str = to_failure_suffix if s["to_failure"] else ""
    name = s["exercise"]["name"]
    return f"{name} \u2014 {s['reps']}\u00d7{weight_str}{rpe_str}{failure_str}"


def _fmt_duration(started_at: str, ended_at: str | None) -> str:
    start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    end = datetime.fromisoformat(ended_at.replace("Z", "+00:00")) if ended_at else datetime.now(timezone.utc)  # noqa: UP017
    minutes = int((end - start).total_seconds() // 60)
    if minutes < 60:
        return f"{minutes} min"
    return f"{minutes // 60}h {minutes % 60}min"


def _fmt_date(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.strftime("%b %d, %Y  %H:%M")


_EQUIP_FILTERS = ["all", "barbell", "dumbbell", "machine", "cable", "bodyweight", "ab_wheel"]


def session_view(page: ft.Page) -> ft.View:
    lang = page.session.store.get("lang") or "en"
    tr = Translator(lang)
    token: str = page.session.store.get("access_token")

    # ── restore saved state ────────────────────────────────────────────────────
    _saved_equip: str = page.session.store.get("session_equip_filter") or "all"
    _saved_exercise: str | None = page.session.store.get("session_exercise_id")

    rpe_labels: dict[str, str] = {
        "no_reps_left": tr("session.rpe_no_reps_left"),
        "could_do_1": tr("session.rpe_could_do_1"),
        "could_do_2": tr("session.rpe_could_do_2"),
        "could_do_3": tr("session.rpe_could_do_3"),
        "could_do_4_5": tr("session.rpe_could_do_4_5"),
        "very_light": tr("session.rpe_very_light"),
    }

    def _tr_set_label(s: dict) -> str:
        return _set_label(
            s,
            rpe_labels=rpe_labels,
            bw_abbrev=tr("session.bw_abbrev"),
            rpe_prefix=tr("session.rpe_prefix"),
            to_failure_suffix=tr("session.to_failure_suffix"),
        )

    # ── state ──────────────────────────────────────────────────────────────────
    active_session: dict | None = None
    _all_exercises: list[dict] = []
    _equip_filter: list[str] = [_saved_equip]

    # ── shared controls ────────────────────────────────────────────────────────
    body = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
    error_text = ft.Text("", color=ft.Colors.ERROR, size=13)
    end_btn = ft.IconButton(
        ft.Icons.STOP_CIRCLE,
        tooltip=tr("session.end_tooltip"),
        visible=False,
        on_click=lambda _: page.run_task(_do_end),
    )

    # ── add-set form fields ────────────────────────────────────────────────────
    exercise_dd = ft.Dropdown(label=tr("session.exercise"), expand=True)
    reps_field = ft.TextField(label=tr("session.reps"), keyboard_type=ft.KeyboardType.NUMBER, width=80)
    weight_field = ft.TextField(label=tr("session.weight"), keyboard_type=ft.KeyboardType.NUMBER, width=110)
    bw_check = ft.Checkbox(label=tr("session.bw_counted"), value=False, tooltip=tr("tooltip.bw_counted"))
    failure_check = ft.Checkbox(label=tr("session.to_failure"), value=False, tooltip=tr("tooltip.to_failure"))
    rpe_dd = ft.Dropdown(
        label=tr("session.rpe"),
        width=200,
        options=[ft.dropdown.Option(k, v) for k, v in rpe_labels.items()],
    )
    rpe_info_btn = ft.IconButton(ft.Icons.INFO_OUTLINE, tooltip=tr("tooltip.rpe"), icon_size=18)

    # ── equipment filter chips ─────────────────────────────────────────────────
    _filter_buttons: dict[str, ft.TextButton] = {}

    def _filter_style(selected: bool) -> ft.ButtonStyle:
        if selected:
            return ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=16),
            )
        return ft.ButtonStyle(
            color=ft.Colors.ON_SURFACE_VARIANT,
            shape=ft.RoundedRectangleBorder(radius=16),
        )

    def _apply_filter(equip: str) -> None:
        _equip_filter[0] = equip
        page.session.store.set("session_equip_filter", equip)
        for key, btn in _filter_buttons.items():
            btn.style = _filter_style(key == equip)
        if equip == "all":
            visible = _all_exercises
        else:
            visible = [ex for ex in _all_exercises if ex.get("equipment_type") == equip]
        exercise_dd.options = [ft.dropdown.Option(str(ex["id"]), localized_exercise_name(ex, lang)) for ex in visible]
        if exercise_dd.value and not any(str(ex["id"]) == exercise_dd.value for ex in visible):
            exercise_dd.value = None
            _exercise_info_panel.content = None
            _exercise_info_panel.visible = False
        page.update()

    for _eq in _EQUIP_FILTERS:
        _label = tr(f"exercise.filter_{_eq}")
        _btn = ft.TextButton(
            content=_label,
            style=_filter_style(_eq == _saved_equip),
            on_click=lambda _, eq=_eq: _apply_filter(eq),
        )
        _filter_buttons[_eq] = _btn

    equip_filter_row = ft.Row(
        list(_filter_buttons.values()),
        scroll=ft.ScrollMode.AUTO,
        spacing=4,
    )

    # ── exercise info panel ────────────────────────────────────────────────────
    _exercise_info_panel = ft.Container(visible=False, padding=ft.Padding.symmetric(horizontal=16))

    def _muscle_chip(muscle_key: str, primary: bool) -> ft.Container:
        color = ft.Colors.TEAL_700 if primary else ft.Colors.GREY_700
        label = tr(f"muscle.{muscle_key}")
        return ft.Container(
            content=ft.Text(label, size=11, color=ft.Colors.WHITE),
            bgcolor=color,
            border_radius=10,
            padding=ft.padding.only(left=8, right=8, top=2, bottom=2),
            margin=ft.Margin(0, 0, 4, 4),
        )

    def _render_exercise_info(ex: dict) -> None:
        equip = ex.get("equipment_type") or ""
        primary = ex.get("primary_muscles") or []
        secondary = ex.get("secondary_muscles") or []
        description = ex.get("description") or ""

        rows: list[ft.Control] = []

        # equipment
        if equip:
            equip_label = tr(f"exercise.filter_{equip}") if equip != "all" else equip
            rows.append(
                ft.Row(
                    [
                        ft.Text(tr("exercise.equipment") + ":", size=12, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(equip_label, size=11, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.BLUE_GREY_700,
                            border_radius=10,
                            padding=ft.padding.only(left=8, right=8, top=2, bottom=2),
                        ),
                    ],
                    spacing=6,
                    wrap=False,
                )
            )

        # primary muscles
        if primary:
            rows.append(
                ft.Row(
                    [ft.Text(tr("exercise.primary_muscles") + ":", size=12, weight=ft.FontWeight.BOLD)],
                    spacing=4,
                )
            )
            rows.append(
                ft.Row(
                    [_muscle_chip(m, primary=True) for m in primary],
                    wrap=True,
                    spacing=0,
                )
            )

        # secondary muscles
        if secondary:
            rows.append(
                ft.Row(
                    [ft.Text(tr("exercise.secondary_muscles") + ":", size=12, weight=ft.FontWeight.BOLD)],
                    spacing=4,
                )
            )
            rows.append(
                ft.Row(
                    [_muscle_chip(m, primary=False) for m in secondary],
                    wrap=True,
                    spacing=0,
                )
            )

        # description
        if description:
            rows.append(ft.Text(tr("exercise.description") + ": " + description, size=12, italic=True))

        _exercise_info_panel.content = ft.Container(
            content=ft.Column(rows, spacing=6),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=8,
            padding=ft.padding.only(left=12, right=12, top=8, bottom=8),
        )
        _exercise_info_panel.visible = bool(rows)
        page.update()

    def _on_exercise_change(e):
        page.session.store.set("session_exercise_id", exercise_dd.value)
        if not exercise_dd.value:
            _exercise_info_panel.visible = False
            page.update()
            return
        ex_id = int(exercise_dd.value)
        matched = next((ex for ex in _all_exercises if ex["id"] == ex_id), None)
        if matched:
            _render_exercise_info(matched)

    exercise_dd.on_select = _on_exercise_change

    # ── render helpers ─────────────────────────────────────────────────────────
    def _set_tile(s: dict) -> ft.ListTile:
        return ft.ListTile(
            title=ft.Text(_tr_set_label(s)),
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=0),
        )

    def _render_idle() -> None:
        end_btn.visible = False
        body.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Button(
                            tr("session.start"),
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=lambda _: page.run_task(_do_start),
                            width=float("inf"),
                        ),
                    ],
                    spacing=16,
                    width=320,
                ),
                padding=ft.padding.only(left=32, right=32, top=32, bottom=16),
                alignment=ft.Alignment(0, 0),
            ),
        ]
        page.update()

    def _render_active() -> None:
        end_btn.visible = True
        ws = active_session
        sets_controls: list = (
            [_set_tile(s) for s in ws["sets"]]
            if ws["sets"]
            else [
                ft.Container(
                    ft.Text(tr("session.no_sets_active"), italic=True, size=13),
                    padding=ft.padding.only(left=16, top=12, bottom=8),
                )
            ]
        )
        form = ft.Column(
            [
                ft.Divider(),
                ft.Container(
                    ft.Text(
                        tr("session.add_set_heading"),
                        size=13,
                        weight=ft.FontWeight.BOLD,
                    ),
                    padding=ft.padding.only(left=16, top=8, bottom=4),
                ),
                ft.Container(
                    equip_filter_row,
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    ft.Row([exercise_dd], expand=True),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                _exercise_info_panel,
                ft.Container(
                    ft.Row([reps_field, weight_field], spacing=12),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    ft.Row([bw_check, failure_check], spacing=24),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    ft.Row([rpe_dd, rpe_info_btn], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    ft.Column(
                        [
                            error_text,
                            ft.Button(
                                tr("session.add_set_btn"),
                                icon=ft.Icons.ADD,
                                on_click=lambda _: page.run_task(_do_add_set),
                                width=float("inf"),
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.only(left=16, right=16, top=4, bottom=24),
                ),
            ],
            spacing=8,
        )
        body.controls = sets_controls + [form]
        page.update()

    # ── async actions ──────────────────────────────────────────────────────────
    async def _load(*, _retried: bool = False) -> None:
        nonlocal active_session, token, _all_exercises
        try:
            config = users_api.get_config(token)
            weight_field.suffix = ft.Text(config.get("weight_unit", "kg"))

            _all_exercises = sessions_api.list_exercises(token)
            # apply saved filter to populate exercise dropdown options
            if _equip_filter[0] == "all":
                _visible = _all_exercises
            else:
                _visible = [ex for ex in _all_exercises if ex.get("equipment_type") == _equip_filter[0]]
            exercise_dd.options = [
                ft.dropdown.Option(str(ex["id"]), localized_exercise_name(ex, lang)) for ex in _visible
            ]
            # restore saved exercise selection if still valid under current filter
            if _saved_exercise and any(str(ex["id"]) == _saved_exercise for ex in _visible):
                exercise_dd.value = _saved_exercise
                _matched = next((ex for ex in _all_exercises if str(ex["id"]) == _saved_exercise), None)
                if _matched:
                    _render_exercise_info(_matched)

            active_session = sessions_api.get_active_session(token)
            if active_session is not None:
                _render_active()
            else:
                _render_idle()
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

    async def _do_start(*, _retried: bool = False) -> None:
        nonlocal active_session, token
        try:
            active_session = sessions_api.start_session(token)
            _render_active()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _do_start(_retried=True)
                return
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            page.update()
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            page.update()

    async def _do_end(*, _retried: bool = False) -> None:
        nonlocal active_session, token
        if active_session is None:
            return
        try:
            sessions_api.end_session(token, active_session["id"])
            active_session = None
            _render_idle()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _do_end(_retried=True)
                return
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            page.update()
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            page.update()

    async def _do_add_set(*, _retried: bool = False) -> None:
        nonlocal active_session, token
        error_text.value = ""

        if not exercise_dd.value:
            error_text.value = tr("session.err_select_exercise")
            page.update()
            return
        reps_str = (reps_field.value or "").strip()
        if not reps_str or not reps_str.isdigit() or int(reps_str) < 1:
            error_text.value = tr("session.err_reps")
            page.update()
            return
        weight_str = (weight_field.value or "").strip()
        try:
            weight = float(weight_str) if weight_str else 0.0
        except ValueError:
            error_text.value = tr("session.err_weight")
            page.update()
            return

        try:
            sessions_api.add_set(
                token=token,
                session_id=active_session["id"],
                exercise_id=int(exercise_dd.value),
                reps=int(reps_str),
                weight=weight,
                bodyweight_counted=bw_check.value or False,
                rpe=rpe_dd.value or None,
                to_failure=failure_check.value or False,
            )
            active_session = sessions_api.get_active_session(token)
            reps_field.value = ""
            weight_field.value = ""
            bw_check.value = False
            failure_check.value = False
            rpe_dd.value = None
            _render_active()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401 and not _retried:
                new_token = await handle_401(page)
                if new_token:
                    token = new_token
                    await _do_add_set(_retried=True)
                return
            error_text.value = tr("common.err_status", code=exc.response.status_code)
            page.update()
        except httpx.RequestError:
            error_text.value = tr("common.err_server")
            page.update()

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Escape":
            page.run_task(page.push_route, "/home")

    page.on_keyboard_event = on_keyboard
    page.run_task(_load)

    return ft.View(
        route="/session",
        appbar=ft.AppBar(
            title=ft.Text(tr("session.title")),
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: page.run_task(page.push_route, "/home"),
            ),
            actions=[
                lang_flag_btn(page),
                ft.IconButton(
                    ft.Icons.HISTORY,
                    tooltip=tr("session.history_tooltip"),
                    on_click=lambda _: page.run_task(page.push_route, "/session-history"),
                ),
                end_btn,
            ],
        ),
        controls=[body],
    )
