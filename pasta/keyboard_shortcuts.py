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
    def on_keyboard(e: ft.KeyboardEvent):
        page.add(
            ft.Text(
                f"Key: {e.key}, Shift: {e.shift}, Control: {e.ctrl}, Alt: {e.alt}, Meta: {e.meta}"
            )
        )

    page.on_keyboard_event = on_keyboard
    page.add(
        ft.Text("Press any key with a combination of CTRL, ALT, SHIFT and META keys...")
    )


ft.run(main)
