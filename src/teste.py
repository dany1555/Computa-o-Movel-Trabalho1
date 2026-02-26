import flet as ft
import uuid
import json
import os
import requests
from typing import Callable
from dotenv import load_dotenv
from flet.security import encrypt, decrypt

# -------------------------
# CONFIG
# -------------------------

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

OAUTH_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API_USER_URL = "https://api.github.com/user"

JSON_STORAGE_KEY = "todo_tasks_list"

# -------------------------
# TASK COMPONENT
# -------------------------

@ft.control
class Task(ft.Column):
    def __init__(
        self,
        task_name: str,
        task_id: str = None,
        completed: bool = False,
        on_status_change: Callable = None,
        on_delete: Callable = None,
    ):
        super().__init__()

        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.task_name = task_name
        self.completed = completed
        self.on_status_change = on_status_change
        self.on_delete = on_delete

        self.checkbox = ft.Checkbox(
            value=self.completed,
            label=self.task_name,
            on_change=self.status_changed,
        )

        self.edit_field = ft.TextField(expand=1)

        self.display_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                self.checkbox,
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.icons.CREATE,
                            on_click=self.edit_clicked,
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            on_click=self.delete_clicked,
                        ),
                    ]
                ),
            ],
        )

        self.edit_row = ft.Row(
            visible=False,
            controls=[
                self.edit_field,
                ft.IconButton(
                    icon=ft.icons.DONE,
                    icon_color=ft.colors.GREEN,
                    on_click=self.save_clicked,
                ),
            ],
        )

        self.controls = [self.display_row, self.edit_row]

    def edit_clicked(self, e):
        self.edit_field.value = self.checkbox.label
        self.display_row.visible = False
        self.edit_row.visible = True
        self.update()

    def save_clicked(self, e):
        self.checkbox.label = self.edit_field.value
        self.task_name = self.edit_field.value
        self.display_row.visible = True
        self.edit_row.visible = False
        if self.on_status_change:
            self.on_status_change()
        self.update()

    def status_changed(self, e):
        self.completed = self.checkbox.value
        if self.on_status_change:
            self.on_status_change()

    def delete_clicked(self, e):
        if self.on_delete:
            self.on_delete(self)


# -------------------------
# TODO APP
# -------------------------

@ft.control
class TodoApp(ft.Column):
    def __init__(self, page: ft.Page, user_id: str):
        super().__init__()

        self.page = page
        self.user_id = user_id

        self.new_task = ft.TextField(hint_text="Nova tarefa...", expand=True)
        self.tasks = ft.Column()

        self.controls = [
            ft.Text(f"Utilizador ID: {self.user_id}", size=12),
            ft.Row(
                controls=[
                    self.new_task,
                    ft.FloatingActionButton(
                        icon=ft.icons.ADD,
                        on_click=self.add_clicked,
                    ),
                ]
            ),
            self.tasks,
            ft.ElevatedButton("Logout", on_click=self.logout),
        ]

        self.load_tasks()

    def storage_key(self):
        return f"{JSON_STORAGE_KEY}_{self.user_id}"

    def load_tasks(self):
        if not SECRET_KEY:
            return

        stored = self.page.client_storage.get(self.storage_key())
        if stored:
            decrypted = decrypt(stored, SECRET_KEY)
            if isinstance(decrypted, bytes):
                decrypted = decrypted.decode("utf-8")
            tasks = json.loads(decrypted)

            for t in tasks:
                self.add_task_to_ui(
                    t["task_name"], t["task_id"], t["completed"]
                )

    def save_tasks(self):
        if not SECRET_KEY:
            return

        tasks_list = [
            {
                "task_id": t.task_id,
                "task_name": t.task_name,
                "completed": t.completed,
            }
            for t in self.tasks.controls
        ]

        encrypted = encrypt(json.dumps(tasks_list), SECRET_KEY)
        self.page.client_storage.set(self.storage_key(), encrypted)

    def add_task_to_ui(self, name, task_id=None, completed=False):
        task = Task(
            task_name=name,
            task_id=task_id,
            completed=completed,
            on_status_change=self.save_tasks,
            on_delete=self.delete_task,
        )
        self.tasks.controls.append(task)

    def add_clicked(self, e):
        if self.new_task.value.strip() == "":
            return
        self.add_task_to_ui(self.new_task.value)
        self.new_task.value = ""
        self.save_tasks()
        self.update()

    def delete_task(self, task):
        self.tasks.controls.remove(task)
        self.save_tasks()
        self.update()

    def logout(self, e):
        self.page.go("/")
        self.page.views.clear()
        show_login(self.page)


# -------------------------
# MAIN
# -------------------------

def main(page: ft.Page):
    page.title = "To-Do OAuth App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def route_change(route):
        if page.route.startswith("/oauth_callback"):
            code = page.query_params.get("code")

            if not code:
                return

            token_response = requests.post(
                TOKEN_URL,
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )

            access_token = token_response.json().get("access_token")

            if not access_token:
                print("Erro ao obter token")
                return

            user_response = requests.get(
                API_USER_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            user_id = str(user_response.json().get("id"))

            page.views.clear()
            page.views.append(
                ft.View("/", controls=[TodoApp(page, user_id)])
            )
            page.update()

    page.on_route_change = route_change
    page.go(page.route)

    show_login(page)


def show_login(page: ft.Page):
    def login_clicked(e):
        state = str(uuid.uuid4())

        auth_url = (
            f"{OAUTH_URL}"
            f"?client_id={GITHUB_CLIENT_ID}"
            f"&redirect_uri=http://localhost:8550/oauth_callback"
            f"&scope=read:user"
            f"&state={state}"
        )

        page.launch_url(auth_url)

    page.views.append(
        ft.View(
            "/",
            controls=[
                ft.Column(
                    [
                        ft.Text("To-Do App", size=30),
                        ft.ElevatedButton(
                            "Login com GitHub",
                            icon=ft.icons.LOGIN,
                            on_click=login_clicked,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            ],
        )
    )

    page.update()


ft.app(
    target=main,
    host="0.0.0.0",
    port=8550
)