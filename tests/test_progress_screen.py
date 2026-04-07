#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/04/07 00:00:00.000000
Revised: 2026/04/07 13:15:38.682663
"""

import pytest

from ximrato_app.screens.progress import _BODY_METRICS, _adapt_body_entries

# ---------------------------------------------------------------------------
# _BODY_METRICS
# ---------------------------------------------------------------------------


def test_body_metrics_contains_all_types():
    assert set(_BODY_METRICS) == {"weight", "waist", "chest", "hips", "neck", "arms", "thighs"}


def test_body_metrics_weight_first():
    assert _BODY_METRICS[0] == "weight"


def test_body_metrics_length():
    assert len(_BODY_METRICS) == 7


def test_body_metrics_no_duplicates():
    assert len(_BODY_METRICS) == len(set(_BODY_METRICS))


# ---------------------------------------------------------------------------
# _adapt_body_entries
# ---------------------------------------------------------------------------


def _make_entry(metric_type: str, logged_at: str, value: float) -> dict:
    return {"metric_type": metric_type, "logged_at": logged_at, "value": value}


def test_adapt_body_entries_filters_by_type():
    entries = [
        _make_entry("weight", "2026-04-01T10:00:00Z", 75.0),
        _make_entry("waist", "2026-04-01T10:00:00Z", 80.0),
        _make_entry("weight", "2026-04-05T10:00:00Z", 74.5),
    ]
    result = _adapt_body_entries(entries, "weight")
    assert len(result) == 2
    assert all(e["max_weight"] in (75.0, 74.5) for e in result)


def test_adapt_body_entries_returns_empty_for_unknown_type():
    entries = [_make_entry("weight", "2026-04-01T10:00:00Z", 75.0)]
    assert _adapt_body_entries(entries, "neck") == []


def test_adapt_body_entries_returns_empty_for_no_entries():
    assert _adapt_body_entries([], "weight") == []


def test_adapt_body_entries_sorted_by_date():
    entries = [
        _make_entry("weight", "2026-04-05T10:00:00Z", 74.5),
        _make_entry("weight", "2026-04-01T10:00:00Z", 75.0),
        _make_entry("weight", "2026-04-03T10:00:00Z", 74.8),
    ]
    result = _adapt_body_entries(entries, "weight")
    dates = [e["date"] for e in result]
    assert dates == sorted(dates)


def test_adapt_body_entries_date_truncated_to_10_chars():
    entries = [_make_entry("weight", "2026-04-01T10:00:00Z", 75.0)]
    result = _adapt_body_entries(entries, "weight")
    assert result[0]["date"] == "2026-04-01"


def test_adapt_body_entries_value_mapped_to_max_weight_key():
    entries = [_make_entry("waist", "2026-04-01T10:00:00Z", 82.5)]
    result = _adapt_body_entries(entries, "waist")
    assert result[0]["max_weight"] == 82.5


def test_adapt_body_entries_mixed_types_only_returns_requested():
    entries = [
        _make_entry("chest", "2026-04-01T10:00:00Z", 95.0),
        _make_entry("hips", "2026-04-01T10:00:00Z", 90.0),
        _make_entry("chest", "2026-04-06T10:00:00Z", 94.5),
    ]
    result = _adapt_body_entries(entries, "chest")
    assert len(result) == 2
    assert all(e["max_weight"] in (95.0, 94.5) for e in result)


@pytest.mark.parametrize("metric", ["weight", "waist", "chest", "hips", "neck", "arms", "thighs"])
def test_adapt_body_entries_works_for_all_metric_types(metric):
    entries = [_make_entry(metric, "2026-04-01T10:00:00Z", 50.0)]
    result = _adapt_body_entries(entries, metric)
    assert len(result) == 1
    assert result[0]["max_weight"] == 50.0
