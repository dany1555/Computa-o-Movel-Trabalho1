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
    async def add_clicked(e):
        page.add(ft.Checkbox(label=new_task.value))
        new_task.value = ""
        await new_task.focus()

    new_task = ft.TextField(hint_text="Whats needs to be done?", width=300)
    page.add(
        ft.Row(
            controls=[new_task, ft.Button(content="Add", on_click=add_clicked)]
        )
    )


ft.run(main)
