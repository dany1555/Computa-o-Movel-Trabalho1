"""Suporte simples para fecho limpo de apps Flet no Windows.

Uso recomendado:
1. `import flet as ft`
2. `from flet_windows_shutdown import patch_flet_run; patch_flet_run()`
3. continuar a usar `ft.run(main)` normalmente
"""

from __future__ import annotations

import asyncio
import inspect
import sys
from typing import Any, Callable

MainCallable = Callable[[Any], Any]


class AsyncioShutdownNoiseFilter:
    """Gere o filtro de ruído de encerramento do asyncio.

    Responsabilidade única:
    - suprimir apenas o erro conhecido (`WinError 10022`) no fecho do loop.
    """

    _LOOP_FILTER_FLAG = "_flet_shutdown_filter_installed"

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.previous_handler = loop.get_exception_handler()

    @classmethod
    def install_on_running_loop(cls) -> None:
        """Instala o filtro no loop atual, se existir e se ainda não estiver ativo."""
        if sys.platform != "win32":
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        if getattr(loop, cls._LOOP_FILTER_FLAG, False):
            return

        cls(loop).install()

    @staticmethod
    def _is_known_shutdown_noise(context: dict[str, Any]) -> bool:
        """Deteta o padrão específico de erro de fecho no Windows."""
        exc = context.get("exception")
        handle = context.get("handle")
        return (
            isinstance(exc, OSError)
            and getattr(exc, "winerror", None) == 10022
            and "_call_connection_lost" in str(handle)
        )

    def install(self) -> None:
        """Ativa o handler de exceções com fallback para o handler anterior."""
        self.loop.set_exception_handler(self._exception_handler)
        setattr(self.loop, self._LOOP_FILTER_FLAG, True)

    def _exception_handler(
        self, loop: asyncio.AbstractEventLoop, context: dict[str, Any]
    ) -> None:
        if self._is_known_shutdown_noise(context):
            return

        if self.previous_handler is not None:
            self.previous_handler(loop, context)
        else:
            loop.default_exception_handler(context)


class WindowCloseResolver:
    """Gere a resolução do evento de fecho da janela Flet.

    Responsabilidade única:
    - ao receber `CLOSE`, chamar `page.window.destroy()` de forma explícita.
    """

    _PAGE_HOOK_FLAG = "_flet_close_hook_installed"

    def __init__(self, page: Any, ft_module: Any):
        self.page = page
        self.ft = ft_module
        self.previous_handler = page.window.on_event

    def install(self) -> None:
        """Liga o handler da janela se ainda não estiver instalado."""
        if getattr(self.page, self._PAGE_HOOK_FLAG, False):
            return

        self.page.window.prevent_close = True
        self.page.window.on_event = self.on_window_event
        setattr(self.page, self._PAGE_HOOK_FLAG, True)

    async def on_window_event(self, event: Any) -> None:
        """Encadeia handler anterior e resolve o evento de fecho."""
        if self.previous_handler is not None:
            result = self.previous_handler(event)
            if inspect.isawaitable(result):
                await result

        if event.type == self.ft.WindowEventType.CLOSE:
            await self.page.window.destroy()


class MainCallableWrapperFactory:
    """Cria wrappers para `main(page)` preservando natureza síncrona/assíncrona.

    Isto evita warnings do tipo "coroutine was never awaited" em versões
    do Flet que distinguem o `main` com base no tipo da função.
    """

    def __init__(self, ft_module: Any):
        self.ft = ft_module

    def _prepare_page(self, page: Any) -> None:
        """Aplica configurações de runtime antes de executar o `main`."""
        AsyncioShutdownNoiseFilter.install_on_running_loop()
        WindowCloseResolver(page, self.ft).install()

    def wrap(self, main: MainCallable) -> MainCallable:
        """Devolve wrapper compatível com o tipo original de `main`."""
        if inspect.iscoroutinefunction(main):
            return self._wrap_async(main)
        return self._wrap_sync(main)

    def _wrap_async(self, main: MainCallable) -> MainCallable:
        async def wrapped(page: Any) -> None:
            self._prepare_page(page)
            await main(page)

        return wrapped

    def _wrap_sync(self, main: MainCallable) -> MainCallable:
        def wrapped(page: Any) -> Any:
            self._prepare_page(page)
            return main(page)

        return wrapped


class FletRunPatcher:
    """Aplica patch em `flet.run` mantendo API simples para os exemplos."""

    _PATCH_FLAG = "_windows_clean_run_patched"

    def __init__(self, ft_module: Any):
        self.ft = ft_module

    def apply(self) -> None:
        """Substitui `ft.run` por versão patched (idempotente)."""
        if sys.platform != "win32":
            return

        if getattr(self.ft, self._PATCH_FLAG, False):
            return

        original_run = self.ft.run

        def patched_run(main: MainCallable, *args: Any, **kwargs: Any) -> Any:
            wrapped_main = MainCallableWrapperFactory(self.ft).wrap(main)
            return original_run(wrapped_main, *args, **kwargs)

        self.ft.run = patched_run
        setattr(self.ft, self._PATCH_FLAG, True)


def patch_flet_run() -> None:
    """API pública: aplica patch em `flet.run` para o processo atual."""
    import flet as ft

    FletRunPatcher(ft).apply()
