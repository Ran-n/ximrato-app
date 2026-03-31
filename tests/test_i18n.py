#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/27 10:30:00.000000
Revised: 2026/03/27 19:28:37.702249
"""

from unittest.mock import patch

import pytest

from ximrato_app.i18n import _CATALOGS, Translator
from ximrato_app.i18n.en import STRINGS as EN
from ximrato_app.i18n.es import STRINGS as ES
from ximrato_app.i18n.gl import STRINGS as GL

# ---------------------------------------------------------------------------
# Translator — basic lookup
# ---------------------------------------------------------------------------


def test_known_key_en():
    assert Translator("en")("common.save") == EN["common.save"]


def test_known_key_gl():
    assert Translator("gl")("common.save") == GL["common.save"]


def test_known_key_es():
    assert Translator("es")("common.save") == ES["common.save"]


def test_unknown_lang_falls_back_to_en():
    assert Translator("fr")("common.save") == EN["common.save"]


def test_empty_lang_falls_back_to_en():
    assert Translator("")("common.save") == EN["common.save"]


def test_key_missing_from_lang_falls_back_to_en():
    incomplete_gl = {k: v for k, v in GL.items() if k != "common.save"}
    with patch.dict(_CATALOGS, {"gl": incomplete_gl}):
        assert Translator("gl")("common.save") == EN["common.save"]


def test_key_not_in_any_catalog_returns_key():
    assert Translator("en")("nonexistent.key.xyz") == "nonexistent.key.xyz"


def test_key_not_in_any_catalog_with_unknown_lang_returns_key():
    assert Translator("zz")("totally.unknown.key") == "totally.unknown.key"


# ---------------------------------------------------------------------------
# Translator — format kwargs
# ---------------------------------------------------------------------------


def test_format_kwargs_interpolated():
    result = Translator("en")("common.err_status", code=404)
    assert "404" in result


def test_format_kwargs_interpolated_in_gl():
    result = Translator("gl")("common.err_status", code=500)
    assert "500" in result


def test_no_kwargs_returns_raw_string():
    result = Translator("en")("common.save")
    assert result == EN["common.save"]
    assert "{" not in result


# ---------------------------------------------------------------------------
# Translator — lang property
# ---------------------------------------------------------------------------


def test_lang_property_returns_lang():
    assert Translator("gl").lang == "gl"


def test_lang_property_falls_back_for_unknown():
    assert Translator("zz").lang == "en"


def test_default_lang_is_en():
    assert Translator().lang == "en"


# ---------------------------------------------------------------------------
# Catalog completeness — every EN key must exist in every other catalog
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lang,catalog", [("gl", GL), ("es", ES)])
def test_all_en_keys_present_in_catalog(lang, catalog):
    missing = set(EN) - set(catalog)
    assert not missing, f"{lang.upper()} is missing keys: {sorted(missing)}"


@pytest.mark.parametrize("lang,catalog", [("gl", GL), ("es", ES)])
def test_no_extra_keys_in_catalog(lang, catalog):
    extra = set(catalog) - set(EN)
    assert not extra, f"{lang.upper()} has unknown keys: {sorted(extra)}"


# ---------------------------------------------------------------------------
# Catalog values — format placeholders consistent with EN
# ---------------------------------------------------------------------------


def test_format_placeholder_consistent_across_langs():
    """Keys that use {code} in EN must also use {code} in GL and ES."""
    for key, en_val in EN.items():
        if "{code}" in en_val:
            for lang, catalog in [("gl", GL), ("es", ES)]:
                val = catalog.get(key, "")
                assert "{code}" in val, f"{lang.upper()} key '{key}' missing {{code}} placeholder"


def test_distance_unit_placeholder_consistent():
    """cardio.distance_unit uses {unit} in all catalogs."""
    for lang, catalog in [("gl", GL), ("es", ES)]:
        assert "{unit}" in catalog.get("cardio.distance_unit", ""), (
            f"{lang.upper()} cardio.distance_unit missing {{unit}} placeholder"
        )
