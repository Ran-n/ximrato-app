#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 13:25:00.000000
Revised: 2026/03/27 19:28:37.267179
"""

import pytest

from ximrato_app.screens.session import RPE_LABELS, _fmt_date, _fmt_duration, _set_label

# ---------------------------------------------------------------------------
# _fmt_duration
# ---------------------------------------------------------------------------


def test_fmt_duration_under_60_min():
    assert _fmt_duration("2026-03-20T10:00:00Z", "2026-03-20T10:45:00Z") == "45 min"


def test_fmt_duration_exact_60_min():
    assert _fmt_duration("2026-03-20T10:00:00Z", "2026-03-20T11:00:00Z") == "1h 0min"


def test_fmt_duration_over_60_min():
    assert _fmt_duration("2026-03-20T10:00:00Z", "2026-03-20T11:30:00Z") == "1h 30min"


def test_fmt_duration_zero_minutes():
    assert _fmt_duration("2026-03-20T10:00:00Z", "2026-03-20T10:00:30Z") == "0 min"


def test_fmt_duration_no_end_uses_now():
    result = _fmt_duration("2026-03-20T10:00:00Z", None)
    assert isinstance(result, str)
    assert "min" in result


def test_fmt_duration_timezone_offset():
    result = _fmt_duration("2026-03-20T10:00:00+00:00", "2026-03-20T10:45:00+00:00")
    assert result == "45 min"


# ---------------------------------------------------------------------------
# _fmt_date
# ---------------------------------------------------------------------------


def test_fmt_date_formats_correctly():
    assert _fmt_date("2026-03-20T10:30:00Z") == "Mar 20, 2026  10:30"


def test_fmt_date_handles_timezone_offset():
    assert _fmt_date("2026-03-20T10:30:00+00:00") == "Mar 20, 2026  10:30"


def test_fmt_date_midnight():
    assert _fmt_date("2026-01-01T00:00:00Z") == "Jan 01, 2026  00:00"


def test_fmt_date_end_of_year():
    assert _fmt_date("2026-12-31T23:59:00Z") == "Dec 31, 2026  23:59"


# ---------------------------------------------------------------------------
# RPE_LABELS completeness
# ---------------------------------------------------------------------------


_EXPECTED_RPE_KEYS = {
    "no_reps_left",
    "could_do_1",
    "could_do_2",
    "could_do_3",
    "could_do_4_5",
    "very_light",
}


def test_rpe_labels_has_all_expected_keys():
    assert set(RPE_LABELS.keys()) == _EXPECTED_RPE_KEYS


@pytest.mark.parametrize("key", sorted(_EXPECTED_RPE_KEYS))
def test_rpe_label_value_is_non_empty_string(key):
    assert isinstance(RPE_LABELS[key], str)
    assert RPE_LABELS[key]


# ---------------------------------------------------------------------------
# _set_label — helpers
# ---------------------------------------------------------------------------


def _make_set(exercise_name="Squat", reps=10, weight=60.0, rpe=None, to_failure=False):
    return {
        "exercise": {"name": exercise_name},
        "reps": reps,
        "weight": weight,
        "rpe": rpe,
        "to_failure": to_failure,
    }


# ---------------------------------------------------------------------------
# _set_label — basic formatting
# ---------------------------------------------------------------------------


def test_set_label_with_weight():
    assert _set_label(_make_set(weight=60.0, reps=10)) == "Squat — 10×60"


def test_set_label_bodyweight():
    assert _set_label(_make_set(weight=0, reps=15)) == "Squat — 15×BW"


def test_set_label_decimal_weight_stripped():
    label = _set_label(_make_set(weight=60.0))
    assert "60.0" not in label
    assert "60" in label


def test_set_label_fractional_weight():
    assert "22.5" in _set_label(_make_set(weight=22.5))


def test_set_label_no_rpe_no_failure():
    label = _set_label(_make_set(rpe=None, to_failure=False))
    assert "RPE" not in label
    assert "failure" not in label


# ---------------------------------------------------------------------------
# _set_label — RPE
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(_EXPECTED_RPE_KEYS))
def test_set_label_includes_rpe_value(key):
    label = _set_label(_make_set(rpe=key))
    assert RPE_LABELS[key] in label


def test_set_label_rpe_uses_prefix():
    label = _set_label(_make_set(rpe="no_reps_left"))
    assert "RPE" in label


# ---------------------------------------------------------------------------
# _set_label — to_failure
# ---------------------------------------------------------------------------


def test_set_label_with_to_failure():
    assert "to failure" in _set_label(_make_set(to_failure=True))


def test_set_label_all_options():
    label = _set_label(_make_set(weight=100.0, reps=5, rpe="could_do_1", to_failure=True))
    assert "Squat" in label
    assert "5×100" in label
    assert RPE_LABELS["could_do_1"] in label
    assert "to failure" in label


# ---------------------------------------------------------------------------
# _set_label — i18n injection (custom strings)
# ---------------------------------------------------------------------------


def test_set_label_custom_bw_abbrev():
    # Galician uses "PC" instead of "BW"
    label = _set_label(_make_set(weight=0, reps=10), bw_abbrev="PC")
    assert "PC" in label
    assert "BW" not in label


def test_set_label_custom_rpe_prefix():
    label = _set_label(_make_set(rpe="very_light"), rpe_prefix="Esforzo")
    assert "Esforzo" in label
    assert "RPE" not in label


def test_set_label_custom_to_failure_suffix():
    label = _set_label(_make_set(to_failure=True), to_failure_suffix="  ✓ ao fallo")
    assert "ao fallo" in label


def test_set_label_custom_rpe_labels():
    translated = {k: f"TR_{k}" for k in _EXPECTED_RPE_KEYS}
    label = _set_label(_make_set(rpe="could_do_2"), rpe_labels=translated)
    assert "TR_could_do_2" in label
