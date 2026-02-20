from dataclasses import field
from typing import Callable
import json
import duckdb
import os

import flet as ft


@ft.control
class Task(ft.Column):
    task_name: str = ""
    completed: bool = False
    on_status_change: Callable[[], None] = field(default=lambda: None)
    on_delete: Callable[["Task"], None] = field(default=lambda task: None)

    def init(self):
        self.display_task = ft.Checkbox(
            value=self.completed, label=self.task_name, on_change=self.status_changed
        )
        self.edit_name = ft.TextField(expand=1)

        self.display_view = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.display_task,
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CREATE_OUTLINED,
                            tooltip="Edit To-Do",
                            on_click=self.edit_clicked,
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            tooltip="Delete To-Do",
                            on_click=self.delete_clicked,
                        ),
                    ],
                ),
            ],
        )

        self.edit_view = ft.Row(
            visible=False,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.edit_name,
                ft.IconButton(
                    icon=ft.Icons.DONE_OUTLINE_OUTLINED,
                    icon_color=ft.Colors.GREEN,
                    tooltip="Update To-Do",
                    on_click=self.save_clicked,
                ),
            ],
        )
        self.controls = [self.display_view, self.edit_view]

    def edit_clicked(self, e):
        self.edit_name.value = self.display_task.label
        self.display_view.visible = False
        self.edit_view.visible = True
        self.update()

    def save_clicked(self, e):
        self.display_task.label = self.edit_name.value
        self.display_view.visible = True
        self.edit_view.visible = False
        self.update()
        self.on_status_change()

    def status_changed(self, e):
        self.completed = self.display_task.value
        self.on_status_change()

    def delete_clicked(self, e):
        self.on_delete(self)


@ft.control
class TodoApp(ft.Column):

    def init(self):
        self.new_task = ft.TextField(hint_text="Whats needs to be done?", expand=True)
        self.tasks = ft.Column()
        self.filter = ft.TabBar(
            scrollable=False,
            tabs=[
                ft.Tab(label="all"),
                ft.Tab(label="active"),
                ft.Tab(label="completed"),
            ],
        )
        self.filter_tabs = ft.Tabs(
            length=3,
            selected_index=0,
            on_change=lambda e: self.update(),
            content=self.filter,
        )
        self.width = 600
        self.controls = [
            ft.Row(
                controls=[
                    self.new_task,
                    ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=self.add_clicked),
                ],
            ),
            ft.Column(
                spacing=25,
                controls=[
                    self.filter_tabs,
                    self.tasks,
                    ft.ElevatedButton("Clear completed", on_click=self.clear_completed),
                ],
            ),
        ]

    # Carrega depois que o controle é montado
    def did_mount(self):
        self.load_tasks()
        self.update()

    def save_tasks(self):
        # Monta lista simples
        tasks_data = [
            {"name": t.display_task.label, "completed": t.completed}
            for t in self.tasks.controls
        ]

        # 🔹 Client Storage
        self.page.client_storage.set("tasks", json.dumps(tasks_data))

        # 🔹 DuckDB + Parquet
        con = duckdb.connect()  # cria em memória por padrão
        con.execute("CREATE TABLE IF NOT EXISTS tasks (name VARCHAR, completed BOOLEAN)")
        con.execute("DELETE FROM tasks")

        for task in tasks_data:
            con.execute(
                "INSERT INTO tasks VALUES (?, ?)",
                (task["name"], task["completed"]),
            )

        # Exporta para Parquet
        con.execute("COPY tasks TO 'tasks.parquet' (FORMAT 'parquet')")
        con.close()

    def load_tasks(self):
        tasks_data = []

        # 1️⃣ tenta Client Storage (como nos exemplos da doc) :contentReference[oaicite:4]{index=4}
        stored = self.page.client_storage.get("tasks")
        if stored:
            tasks_data = json.loads(stored)

        # 2️⃣ se não houver, tenta Parquet via DuckDB :contentReference[oaicite:5]{index=5}
        elif os.path.exists("tasks.parquet"):
            con = duckdb.connect()
            result = con.execute("SELECT * FROM read_parquet('tasks.parquet')").fetchall()
            con.close()
            tasks_data = [{"name": r[0], "completed": r[1]} for r in result]

        # Cria as tarefas na UI
        for task in tasks_data:
            self.tasks.controls.append(
                Task(
                    task_name=task["name"],
                    completed=task["completed"],
                    on_status_change=self.task_status_change,
                    on_delete=self.task_delete,
                )
            )

    def add_clicked(self, e):
        if not self.new_task.value:
            return
        task = Task(
            task_name=self.new_task.value,
            on_status_change=self.task_status_change,
            on_delete=self.task_delete,
        )
        self.tasks.controls.append(task)
        self.new_task.value = ""
        self.save_tasks()
        self.update()

    def task_status_change(self):
        self.save_tasks()
        self.update()

    def task_delete(self, task):
        self.tasks.controls.remove(task)
        self.save_tasks()
        self.update()

    def clear_completed(self, e):
        self.tasks.controls = [
            task for task in self.tasks.controls if not task.completed
        ]
        self.save_tasks()
        self.update()

    def before_update(self):
        status = self.filter.tabs[self.filter_tabs.selected_index].label
        for task in self.tasks.controls:
            task.visible = (
                status == "all"
                or (status == "active" and not task.completed)
                or (status == "completed" and task.completed)
            )


def main(page: ft.Page):
    page.title = "To-Do App"
    app = TodoApp()
    page.add(app)


ft.run(main)