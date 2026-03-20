#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:41:15.000000
Revised: 2026/03/20 10:46:06.549931
"""

from unittest.mock import MagicMock

from ximrato_app.api.errors import parse_422


def _mock_response(detail):
    r = MagicMock()
    r.json.return_value = {"detail": detail}
    return r


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


def test_parse_422_empty_list():
    assert parse_422(_mock_response([])) == "Invalid input."


def test_parse_422_not_a_list():
    assert parse_422(_mock_response("string error")) == "Invalid input."


def test_parse_422_missing_msg():
    detail = [{"loc": ["body", "field"]}]
    assert parse_422(_mock_response(detail)) == "field: invalid input"
