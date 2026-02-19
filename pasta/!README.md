# Exemplos Flet (Aulas)

Esta pasta tem exemplos simples de Flet para a aula TP/PL de CM.  
Cada ficheiro é autónomo (PEP-723 metadata) e pode ser executado com o `uv`.

## Ficheiros

- `hello_world.py`: aplicação mínima com um controlo de texto.
- `counter.py`: interface básica de incremento/decremento.
- `counter_timed.py`: atualizações assíncronas ao longo do tempo.
- `checkbox.py`: gestão da mudança de estado de uma checkbox.
- `dropdown.py`: leitura de valores de um dropdown.
- `text_button.py`: validação de entrada e atualização da página.
- `to_do.py`: adição dinâmica de controlos.
- `keyboard_shortcuts.py`: gestão de eventos de teclado.
- `control_refs1.py`: referências diretas a controlos.
- `control_refs2.py`: acesso a controlos com `ft.Ref`.

## Executar um exemplo

Na pasta do projeto:

```bash
uv run checkbox.py
```

Pode executar qualquer outro ficheiro da lista acima.

## Comportamento de encerramento no Windows

Todos os exemplos chamam `patch_flet_run()` de `flet_windows_shutdown.py`
antes de `ft.run(main)`.

Este utilitário existe para reduzir problemas de fecho no Windows com
versões modernas de Python:

- suprime mensagens verbosas de encerramento com `WinError 10022`;
- resolve explicitamente o evento de fecho da janela;
- não altera nada em plataformas que não sejam Windows.

## Notas para estudantes

- Feche a aplicação no botão `X` da janela.
- Se o terminal não devolver o prompt, use `Ctrl+C`.
- Mantenha `flet_windows_shutdown.py` nesta pasta para os imports funcionarem.
