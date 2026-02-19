#!uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "flet[all]>=0.80.5",
# ]
# ///

import flet as ft
import asyncio

# Patch two flet 0.80.5 quirks on app shutdown: asyncio WinError 10022; hung page.window.destroy()
from flet_windows_shutdown import patch_flet_run; patch_flet_run()

async def main(page: ft.Page):
    t = ft.Text()
    page.add(t)  # o mesmo que page.controls.append(t) + page.update()

    for i in range(11):
        t.value = f"Step {i}"
        page.update()  # fora de um evento, é necessário chamar page.update() para atualizar a interface
        await asyncio.sleep(1)


ft.run(main)
