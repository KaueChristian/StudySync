import flet as ft
from models.funcoes import Agenda
import sqlite3 as sq

def loginuser(page: ft.Page):
    page.title = "Sistema de Login"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 600
    page.window.height = 550

    agenda = Agenda()

    def route_change(route):
        page.views.clear()
        
        if page.route == "/login":
            page.views.append(
                ft.View(
                    "/login",
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Login", size=30, weight="bold"),
                                    email_field,
                                    password_field,
                                    login_button,
                                    ft.TextButton(
                                        "Criar nova conta",
                                        on_click=lambda _: page.go("/register")
                                    ),
                                    error_message
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=30,
                        )
                    ],
                    vertical_alignment= ft.MainAxisAlignment.CENTER,
                    horizontal_alignment= ft.CrossAxisAlignment.CENTER
                )
            )
        
        elif page.route == "/register":
            page.views.append(
                ft.View(
                    "/register",
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Registro", size=30, weight="bold"),
                                    name_field,
                                    email_register_field,
                                    password_register_field,
                                    register_button,
                                    ft.TextButton(
                                        "Voltar para Login",
                                        on_click=lambda _: page.go("/login")
                                    ),
                                    register_message
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=30,
                        )
                    ],
                    vertical_alignment= ft.MainAxisAlignment.CENTER,
                    horizontal_alignment= ft.CrossAxisAlignment.CENTER
                )
            )
        
        page.update()

    email_field = ft.TextField(label="Email", width=300)
    password_field = ft.TextField(label="Senha", password=True, width=300)
    error_message = ft.Text("", color="red")

    name_field = ft.TextField(label="Nome completo", width=300)
    email_register_field = ft.TextField(label="Email", width=300)
    password_register_field = ft.TextField(label="Senha", password=True, width=300)
    register_message = ft.Text("", color="green")

    def login(e):
        user_id = agenda.login_user(email_field.value, password_field.value)
        if user_id:
            error_message.value = "Login realizado com sucesso!"
            error_message.color = "green"
            # nav pra tela principal
        else:
            error_message.value = "Email ou senha inválidos!"
            error_message.color = "red"
        page.update()

    def register(e):
        if name_field.value == "" or email_register_field.value == "" or password_register_field.value == "":
            register_message.value = "Preencha todos os campos!"
            register_message.color = "red"
            page.update()
            return
        try:
            user_id = agenda.add_user(
                name_field.value,
                email_register_field.value,
                password_register_field.value
            )
            if user_id:
                register_message.value = "Conta criada com sucesso!"
                register_message.color = "green"
                # page.go("/login")
                page.update()
        except sq.IntegrityError:
            register_message.value = "Este email já está cadastrado!"
            register_message.color = "red"
            page.update()

    login_button = ft.ElevatedButton("Entrar", on_click=login, width=300)
    register_button = ft.ElevatedButton("Criar conta", on_click=register, width=300)

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")

ft.app(target=loginuser)