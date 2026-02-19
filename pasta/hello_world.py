#!uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "flet[all]>=0.80.5",
# ]
# ///

import flet as ft

# Patch two flet 0.80.5 quirks on app shutdown: asyncio WinError 10022; hung page.window.destroy()
from flet_windows_shutdown import patch_flet_run; patch_flet_run()

def main(page: ft.Page):
    t = ft.Text(value="Hello, world!", color="green")
    page.controls.append(t) # ou page.add(t)


ft.run(main)
