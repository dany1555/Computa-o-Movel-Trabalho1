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
    def checkbox_changed(e):
        output_text.value = f"You have learned how to ski: {todo_check.value}."

    output_text = ft.Text()
    todo_check = ft.Checkbox(
        label="ToDo: Learn how to use ski", value=False, on_change=checkbox_changed
    )
    page.add(todo_check, output_text)


ft.run(main)
