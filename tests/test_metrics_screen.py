#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/28 14:44:51.339876
Revised: 2026/03/28 14:44:51.339876
"""

from ximrato_app.screens.metrics import _METRIC_ORDER, _delta_label, _fmt_date

# ---------------------------------------------------------------------------
# _delta_label
# ---------------------------------------------------------------------------


def test_delta_label_positive():
    assert _delta_label(76.0, 75.0) == "\u2191 +1"


def test_delta_label_negative():
    assert _delta_label(74.0, 75.0) == "\u2193 -1"


def test_delta_label_zero():
    assert _delta_label(75.0, 75.0) == "\u2192 \u00b10"


def test_delta_label_positive_fractional():
    assert _delta_label(75.3, 75.1) == "\u2191 +0.2"


def test_delta_label_negative_fractional():
    assert _delta_label(74.8, 75.0) == "\u2193 -0.2"


def test_delta_label_large_positive():
    assert _delta_label(100.0, 80.0) == "\u2191 +20"


def test_delta_label_large_negative():
    assert _delta_label(60.0, 80.0) == "\u2193 -20"


def test_delta_label_arrow_up_in_result():
    result = _delta_label(80.0, 79.0)
    assert "\u2191" in result
    assert "+" in result


def test_delta_label_arrow_down_in_result():
    result = _delta_label(79.0, 80.0)
    assert "\u2193" in result


def test_delta_label_arrow_right_on_zero():
    result = _delta_label(50.0, 50.0)
    assert "\u2192" in result


# ---------------------------------------------------------------------------
# _METRIC_ORDER
# ---------------------------------------------------------------------------


def test_metric_order_contains_all_types():
    assert set(_METRIC_ORDER) == {
        "weight",
        "waist",
        "chest",
        "hips",
        "neck",
        "arms",
        "thighs",
    }


def test_metric_order_weight_first():
    assert _METRIC_ORDER[0] == "weight"


def test_metric_order_length():
    assert len(_METRIC_ORDER) == 7


# ---------------------------------------------------------------------------
# _fmt_date
# ---------------------------------------------------------------------------


def test_fmt_date_z_suffix():
    assert _fmt_date("2026-03-25T10:30:00Z") == "Mar 25, 2026  10:30"


def test_fmt_date_offset():
    assert _fmt_date("2026-03-25T10:30:00+00:00") == "Mar 25, 2026  10:30"


def test_fmt_date_midnight():
    assert _fmt_date("2026-01-01T00:00:00Z") == "Jan 01, 2026  00:00"
