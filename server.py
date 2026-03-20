#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 11:30:12.376789
Revised: 2026/03/20 11:30:38.546684
"""

# ASGI entry point — run with:
#   uv run uvicorn server:app --port 8080 --reload
#
# Supports path-based routing, so /login, /home, etc. all work directly.

import flet as ft

from main import main

app = ft.run(main, export_asgi_app=True)
