import os
import flet as ft
from flet.auth.providers import GitHubOAuthProvider

def main(page: ft.Page):
    page.title = "To-Do App Autenticada"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    provider = GitHubOAuthProvider(
        client_id=os.getenv("GITHUB_CLIENT_ID"),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
        redirect_url="http://localhost:8550/oauth_callback",
    )

    # CORREÇÃO: O handler tem de ser 'async' e o login tem de ter 'await'
    async def login_button_click(e):
        await page.login(provider, scope=["public_repo"])

    def on_login(e: ft.LoginEvent):
        if not e.error:
            toggle_login_buttons()
        else:
            print(f"Erro no login: {e.error}")

    # CORREÇÃO: O logout também pode precisar de 'await' dependendo da versão
    async def logout_button_click(e):
        await page.logout()

    def on_logout(e):
        toggle_login_buttons()

    def toggle_login_buttons():
        is_logged_in = page.auth is not None
        
        # Limpar controlos para evitar duplicados
        page.controls.clear()
        
        if is_logged_in:
            # Obter ID do utilizador logado
            user_id = str(page.auth.user.id)
            
            # Criar a App (Certifique-se que a classe TodoApp existe no seu ficheiro)
            app = TodoApp(page, user_id)
            
            # Adicionar logout e app
            page.add(logout_button, app)
        else:
            # Mostrar botão de login
            page.add(login_button)
            
        page.update()

    # Criar os botões
    login_button = ft.Button("Login with GitHub", on_click=login_button_click)
    logout_button = ft.Button("Logout", on_click=logout_button_click)
    
    # Verificar estado inicial
    toggle_login_buttons()

    # Definir eventos
    page.on_login = on_login
    page.on_logout = on_logout

# Iniciar aplicação
ft.run(main, port=8550, view=ft.AppView.WEB_BROWSER)