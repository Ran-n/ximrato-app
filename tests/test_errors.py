#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:41:15.000000
Revised: 2026/03/27 19:28:37.079008
"""

from unittest.mock import MagicMock

from ximrato_app.api.errors import parse_422


def _mock_response(detail):
    r = MagicMock()
    r.json.return_value = {"detail": detail}
    return r


# ---------------------------------------------------------------------------
# happy path
# ---------------------------------------------------------------------------


def test_parse_422_with_loc_and_msg():
    detail = [{"loc": ["body", "email"], "msg": "value is not a valid email address"}]
    assert parse_422(_mock_response(detail)) == "email: value is not a valid email address"


def test_parse_422_filters_body_from_loc():
    detail = [{"loc": ["body", "username"], "msg": "field required"}]
    result = parse_422(_mock_response(detail))
    assert "body" not in result
    assert "username" in result


def test_parse_422_nested_loc():
    detail = [{"loc": ["body", "address", "zip"], "msg": "invalid"}]
    assert parse_422(_mock_response(detail)) == "address → zip: invalid"


def test_parse_422_empty_loc():
    detail = [{"loc": [], "msg": "something bad"}]
    assert parse_422(_mock_response(detail)) == "something bad"


def test_parse_422_only_body_in_loc():
    # ["body"] → after filtering "body" nothing remains → return msg only
    detail = [{"loc": ["body"], "msg": "root level error"}]
    assert parse_422(_mock_response(detail)) == "root level error"


def test_parse_422_integer_in_loc():
    # Array indices appear as integers; they should be kept (only "body" is filtered)
    detail = [{"loc": ["body", 0, "field"], "msg": "required"}]
    result = parse_422(_mock_response(detail))
    assert "0" in result
    assert "field" in result


def test_parse_422_missing_msg():
    detail = [{"loc": ["body", "field"]}]
    assert parse_422(_mock_response(detail)) == "field: invalid input"


# ---------------------------------------------------------------------------
# only the first error entry is used
# ---------------------------------------------------------------------------


def test_parse_422_multiple_errors_uses_first():
    detail = [
        {"loc": ["body", "email"], "msg": "invalid email"},
        {"loc": ["body", "username"], "msg": "too short"},
    ]
    result = parse_422(_mock_response(detail))
    assert "email" in result
    assert "invalid email" in result
    assert "username" not in result


# ---------------------------------------------------------------------------
# degenerate inputs
# ---------------------------------------------------------------------------


def test_parse_422_empty_list():
    assert parse_422(_mock_response([])) == "Invalid input."


def test_parse_422_not_a_list():
    assert parse_422(_mock_response("string error")) == "Invalid input."


def test_parse_422_none_detail():
    assert parse_422(_mock_response(None)) == "Invalid input."
