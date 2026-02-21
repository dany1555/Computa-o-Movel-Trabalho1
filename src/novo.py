import flet as ft
from dataclasses import field
from typing import Callable
import uuid
import json
import os
import duckdb
from dotenv import load_dotenv
from flet.security import encrypt, decrypt

# Carregar chave do ficheiro .env
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

# Ficheiros
PARQUET_FILE = "tasks.parquet"
JSON_FILE = "tasks_local.json"
JSON_STORAGE_KEY = "todo_tasks_list"

@ft.control
class Task(ft.Column):
    def __init__(self, task_name: str, task_id: str = None, completed: bool = False, on_status_change: Callable = None, on_delete: Callable = None):
        super().__init__()
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.task_name = task_name
        self.completed = completed
        self.on_status_change = on_status_change
        self.on_delete = on_delete

        self.display_task = ft.Checkbox(
            value=self.completed, 
            label=self.task_name, 
            on_change=self.status_changed
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
                        ft.IconButton(icon=ft.Icons.CREATE_OUTLINED, tooltip="Edit To-Do", on_click=self.edit_clicked),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Delete To-Do", on_click=self.delete_clicked),
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
                ft.IconButton(icon=ft.Icons.DONE_OUTLINE_OUTLINED, icon_color=ft.Colors.GREEN, tooltip="Update To-Do", on_click=self.save_clicked),
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
        self.task_name = self.edit_name.value
        self.display_view.visible = True
        self.edit_view.visible = False
        self.update()
        if self.on_status_change: 
            self.on_status_change()

    def status_changed(self, e):
        self.completed = self.display_task.value
        if self.on_status_change: 
            self.on_status_change()

    def delete_clicked(self, e):
        if self.on_delete:
            self.on_delete(self)


@ft.control
class TodoApp(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page_ref = page 
        
        self.new_task = ft.TextField(hint_text="Whats needs to be done?", expand=True)
        self.tasks = ft.Column()

        self.filter = ft.TabBar(
            scrollable=False,
            tabs=[ft.Tab(label="all"), ft.Tab(label="active"), ft.Tab(label="completed")],
        )

        self.filter_tabs = ft.Tabs(
            length=3, selected_index=0, on_change=lambda e: self.update(), content=self.filter
        )

        self.width = 600
        self.controls = [
            ft.Row(controls=[self.new_task, ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=self.add_clicked)]),
            ft.Column(spacing=25, controls=[self.filter_tabs, self.tasks, ft.Button("Clear completed", on_click=self.clear_completed)]),
        ]
        
        self.load_tasks()

    # --- DuckDB & Client Storage ---

    def load_tasks(self):
        tasks_data = []
        loaded = False
        
        # 1. Client-Side Storage (Browser)
        try:
            if hasattr(self._page_ref, 'client_storage') and SECRET_KEY:
                stored_encrypted = self._page_ref.client_storage.get(JSON_STORAGE_KEY)
                if stored_encrypted:
                    decrypted = decrypt(stored_encrypted, SECRET_KEY)
                    if isinstance(decrypted, bytes):
                        tasks_data = json.loads(decrypted.decode('utf-8'))
                    else:
                        tasks_data = json.loads(decrypted)
                    print("Carregado do Client-Side (Browser) - Desencriptado.")
                    loaded = True
        except: pass

        # 2. Ficheiro Local JSON (Desktop/App)
        if not loaded and os.path.exists(JSON_FILE) and SECRET_KEY:
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    encrypted_data = f.read()
                    if encrypted_data:
                        decrypted = decrypt(encrypted_data, SECRET_KEY)
                        if isinstance(decrypted, bytes):
                            tasks_data = json.loads(decrypted.decode('utf-8'))
                        else:
                            tasks_data = json.loads(decrypted)
                        print("Carregado do ficheiro JSON local - Desencriptado.")
                        loaded = True
            except: pass

        # 3. Ficheiro Parquet (DuckDB) - ENCRIPTADO
        if not loaded and os.path.exists(PARQUET_FILE) and SECRET_KEY:
            try:
                con = duckdb.connect()
                result = con.execute(f"SELECT encrypted_data FROM '{PARQUET_FILE}'").fetchall()
                con.close()
                
                if result and result[0][0]:
                    encrypted_data = result[0][0]
                    decrypted = decrypt(encrypted_data, SECRET_KEY)
                    if isinstance(decrypted, bytes):
                        tasks_data = json.loads(decrypted.decode('utf-8'))
                    else:
                        tasks_data = json.loads(decrypted)
                    print("Carregado do ficheiro Parquet (DuckDB) - Desencriptado.")
            except Exception as e:
                print(f"Erro DuckDB Load: {e}")

        # Popular a UI
        for t in tasks_data:
            self.add_task_to_ui(t.get('task_name'), t.get('task_id'), t.get('completed'))

    def save_tasks(self):
        # Serializar tarefas
        tasks_list = []
        for task in self.tasks.controls:
            tasks_list.append({
                "task_id": task.task_id,
                "task_name": task.task_name,
                "completed": task.completed
            })

        if not SECRET_KEY:
            print("Erro: SECRET_KEY não definida no .env")
            return

        # Encriptar os dados
        json_str = json.dumps(tasks_list)
        encrypted_data = encrypt(json_str, SECRET_KEY)

        # (A) Client-Side Storage
        try:
            if hasattr(self._page_ref, 'client_storage'):
                self._page_ref.client_storage.set(JSON_STORAGE_KEY, encrypted_data)
                print("Salvo no Client-Side (Browser) - Encriptado")
            
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                f.write(encrypted_data)
                
        except Exception as e:
            print(f"Erro armazenamento A: {e}")

        # (B) DuckDB -> Parquet ENCRIPTADO
        try:
            con = duckdb.connect(':memory:')
            
            con.execute("CREATE TABLE tasks (encrypted_data TEXT)")
            con.execute("INSERT INTO tasks VALUES (?)", [encrypted_data])
            
            con.execute(f"COPY tasks TO '{PARQUET_FILE}' (FORMAT PARQUET)")
            
            con.close()
            print(f"Guardado em {PARQUET_FILE} - Encriptado")
        except Exception as e:
            print(f"Erro DuckDB Save: {e}")

    def add_task_to_ui(self, task_name, task_id=None, completed=False):
        task = Task(task_name=task_name, task_id=task_id, completed=completed,
                    on_status_change=self.task_status_change, on_delete=self.task_delete)
        self.tasks.controls.append(task)

    # --- Ações ---
    def add_clicked(self, e):
        self.add_task_to_ui(self.new_task.value)
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
        self.tasks.controls = [task for task in self.tasks.controls if not task.completed]
        self.save_tasks()
        self.update()


    def before_update(self):
        status = self.filter.tabs[self.filter_tabs.selected_index].label
        for task in self.tasks.controls:
            task.visible = (status == "all" or (status == "active" and not task.completed) or (status == "completed" and task.completed))



def main(page: ft.Page):
    page.title = "To-Do App Encriptada"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.update()
    app = TodoApp(page)
    page.add(app)


ft.run(main)