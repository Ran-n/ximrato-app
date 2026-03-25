#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/25 07:52:53.440396
Revised: 2026/03/25 07:52:53.440396
"""

#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/25 00:00:00.000000
Revised: 2026/03/25 00:00:00.000000
"""

from ximrato_app.screens.cardio import (
    _fmt_date,
    _fmt_duration,
    _fmt_elapsed,
    _log_label,
)

# ── _fmt_elapsed ───────────────────────────────────────────────────────────────


def test_fmt_elapsed_under_one_hour():
    assert _fmt_elapsed(0) == "00:00"
    assert _fmt_elapsed(90) == "01:30"
    assert _fmt_elapsed(3599) == "59:59"


def test_fmt_elapsed_exact_one_hour():
    assert _fmt_elapsed(3600) == "1:00:00"


def test_fmt_elapsed_over_one_hour():
    assert _fmt_elapsed(3661) == "1:01:01"
    assert _fmt_elapsed(7384) == "2:03:04"


# ── _fmt_duration ──────────────────────────────────────────────────────────────


def test_fmt_duration_under_60_min():
    assert _fmt_duration(90) == "1min 30s"
    assert _fmt_duration(60) == "1min 00s"


def test_fmt_duration_over_60_min():
    assert _fmt_duration(3661) == "1h 01min 01s"
    assert _fmt_duration(3600) == "1h 00min 00s"


def test_fmt_duration_zero():
    assert _fmt_duration(0) == "0min 00s"


# ── _fmt_date ──────────────────────────────────────────────────────────────────


def test_fmt_date_z_suffix():
    assert _fmt_date("2026-03-25T10:30:00Z") == "Mar 25, 2026  10:30"


def test_fmt_date_offset():
    assert _fmt_date("2026-03-25T10:30:00+00:00") == "Mar 25, 2026  10:30"


# ── _log_label ─────────────────────────────────────────────────────────────────


def _make_log(
    name="Running",
    duration_seconds=1800,
    distance=None,
    avg_heart_rate=None,
    elevation_gain=None,
    stroke_rate=None,
):
    return {
        "exercise": {"name": name},
        "duration_seconds": duration_seconds,
        "distance": distance,
        "avg_heart_rate": avg_heart_rate,
        "elevation_gain": elevation_gain,
        "stroke_rate": stroke_rate,
    }


def test_log_label_required_only():
    label = _log_label(_make_log(), "km")
    assert label == "Running — 30min 00s"


def test_log_label_with_distance():
    label = _log_label(_make_log(distance=5.0), "km")
    assert "5 km" in label


def test_log_label_distance_unit_mi():
    label = _log_label(_make_log(distance=3.1), "mi")
    assert "3.1 mi" in label


def test_log_label_with_hr():
    label = _log_label(_make_log(avg_heart_rate=145), "km")
    assert "145 bpm" in label


def test_log_label_with_elevation():
    label = _log_label(_make_log(elevation_gain=50.0), "km")
    assert "↑50 m" in label


def test_log_label_with_stroke_rate():
    label = _log_label(_make_log(name="Rowing", stroke_rate=28), "km")
    assert "28 spm" in label


def test_log_label_none_fields_omitted():
    label = _log_label(_make_log(), "km")
    assert "bpm" not in label
    assert "spm" not in label
    assert "↑" not in label


def test_log_label_all_fields():
    label = _log_label(
        _make_log(distance=10.0, avg_heart_rate=160, elevation_gain=200.0), "km"
    )
    assert "10 km" in label
    assert "160 bpm" in label
    assert "↑200 m" in label
