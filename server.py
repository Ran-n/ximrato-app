#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 11:30:12.376789
Revised: 2026/03/24 08:52:47.457224
"""

# ASGI entry point — run with:
#   uv run uvicorn server:app --port 8080 --reload
#
# Supports path-based routing, so /login, /home, etc. all work directly.

import flet as ft

from ximrato_app.app import main

app = ft.run(main, export_asgi_app=True)
