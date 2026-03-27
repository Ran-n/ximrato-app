#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/25 12:30:44.797233
Revised: 2026/03/25 12:30:44.797233
"""

from ximrato_app.i18n.en import STRINGS as _EN
from ximrato_app.i18n.es import STRINGS as _ES
from ximrato_app.i18n.gl import STRINGS as _GL

_CATALOGS: dict[str, dict[str, str]] = {"en": _EN, "gl": _GL, "es": _ES}
_SUPPORTED: frozenset[str] = frozenset(_CATALOGS)


class Translator:
    """Per-view translator. Instantiate with the user's language code."""

    def __init__(self, lang: str = "en") -> None:
        self._lang = lang if lang in _SUPPORTED else "en"

    def __call__(self, key: str, **kwargs: object) -> str:
        catalog = _CATALOGS.get(self._lang, _EN)
        s = catalog.get(key) or _EN.get(key, key)
        return s.format(**kwargs) if kwargs else s

    @property
    def lang(self) -> str:
        return self._lang
