#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/03/20 09:03:49.074618
Revised: 2026/03/28 16:15:23.673406
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))

import flet as ft

from ximrato_app.app import main

ft.run(main)
