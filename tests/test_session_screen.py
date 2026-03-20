#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 13:25:00.000000
Revised: 2026/03/20 13:35:28.780552
"""

from ximrato_app.screens.session import RPE_LABELS, _fmt_date, _fmt_duration, _set_label

# ── _fmt_duration ──────────────────────────────────────────────────────────────


def test_fmt_duration_under_60_min():
    result = _fmt_duration("2026-03-20T10:00:00Z", "2026-03-20T10:45:00Z")
    assert result == "45 min"


def test_fmt_duration_exact_60_min():
    result = _fmt_duration("2026-03-20T10:00:00Z", "2026-03-20T11:00:00Z")
    assert result == "1h 0min"


def test_fmt_duration_over_60_min():
    result = _fmt_duration("2026-03-20T10:00:00Z", "2026-03-20T11:30:00Z")
    assert result == "1h 30min"


def test_fmt_duration_no_end_uses_now():
    # With no end time, uses datetime.now(utc) — just check it returns a string
    result = _fmt_duration("2026-03-20T10:00:00Z", None)
    assert isinstance(result, str)
    assert "min" in result


def test_fmt_duration_zero_minutes():
    result = _fmt_duration("2026-03-20T10:00:00Z", "2026-03-20T10:00:30Z")
    assert result == "0 min"


# ── _fmt_date ──────────────────────────────────────────────────────────────────


def test_fmt_date_formats_correctly():
    result = _fmt_date("2026-03-20T10:30:00Z")
    assert result == "Mar 20, 2026  10:30"


def test_fmt_date_handles_timezone_offset():
    # +00:00 and Z should both parse correctly
    result = _fmt_date("2026-03-20T10:30:00+00:00")
    assert result == "Mar 20, 2026  10:30"


# ── _set_label ─────────────────────────────────────────────────────────────────


def _make_set(exercise_name="Squat", reps=10, weight=60.0, rpe=None, to_failure=False):
    return {
        "exercise": {"name": exercise_name},
        "reps": reps,
        "weight": weight,
        "rpe": rpe,
        "to_failure": to_failure,
    }


def test_set_label_with_weight():
    label = _set_label(_make_set(weight=60.0, reps=10))
    assert label == "Squat — 10×60"


def test_set_label_bodyweight():
    label = _set_label(_make_set(weight=0, reps=15))
    assert label == "Squat — 15×BW"


def test_set_label_with_rpe():
    label = _set_label(_make_set(rpe="no_reps_left"))
    assert RPE_LABELS["no_reps_left"] in label


def test_set_label_with_to_failure():
    label = _set_label(_make_set(to_failure=True))
    assert "to failure" in label


def test_set_label_all_options():
    label = _set_label(
        _make_set(weight=100.0, reps=5, rpe="could_do_1", to_failure=True)
    )
    assert "Squat" in label
    assert "5×100" in label
    assert RPE_LABELS["could_do_1"] in label
    assert "to failure" in label


def test_set_label_no_rpe_no_failure():
    label = _set_label(_make_set(rpe=None, to_failure=False))
    assert "RPE" not in label
    assert "failure" not in label


def test_set_label_decimal_weight_stripped():
    # weight=60.0 should show as "60" not "60.0" (uses :g format)
    label = _set_label(_make_set(weight=60.0))
    assert "60.0" not in label
    assert "60" in label


def test_set_label_fractional_weight():
    label = _set_label(_make_set(weight=22.5))
    assert "22.5" in label
