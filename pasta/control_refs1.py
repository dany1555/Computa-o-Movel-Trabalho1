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
    first_name = ft.TextField(label="First name", autofocus=True)
    last_name = ft.TextField(label="Last name")
    greetings = ft.Column()

    async def btn_click(e):
        greetings.controls.append(
            ft.Text(f"Hello, {first_name.value} {last_name.value}!")
        )
        first_name.value = ""
        last_name.value = ""
        await first_name.focus()

    page.add(
        first_name,
        last_name,
        ft.Button(content="Say hello!", on_click=btn_click),
        greetings,
    )


ft.run(main)
