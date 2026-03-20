#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 10:04:44.000000
Revised: 2026/03/20 10:41:15.397651
"""


def parse_422(response) -> str:
    """Return a human-readable string from a Pydantic 422 response."""
    detail = response.json().get("detail", [])
    if isinstance(detail, list) and detail:
        loc = " → ".join(str(p) for p in detail[0].get("loc", []) if p != "body")
        msg = detail[0].get("msg", "invalid input")
        return f"{loc}: {msg}" if loc else msg
    return "Invalid input."
