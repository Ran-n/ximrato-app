#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.074618
Revised: 2026/03/31 08:24:56.113223
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))

import flet as ft

from ximrato_app.main import main

ft.run(main)
