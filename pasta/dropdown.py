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
    def button_clicked(e):
        output_text.value = f"Dropdown value is: {color_dropdown.value}"

    output_text = ft.Text()
    submit_btn = ft.Button(content="Submit", on_click=button_clicked)
    color_dropdown = ft.Dropdown(
        width=100,
        options=[
            ft.DropdownOption(text="Red"),
            ft.DropdownOption(text="Green"),
            ft.DropdownOption(text="Blue"),
        ],
    )
    page.add(color_dropdown, submit_btn, output_text)


ft.run(main)
