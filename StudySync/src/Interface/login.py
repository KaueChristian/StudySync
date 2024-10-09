import flet as ft

def main(page: ft.Page):
    page.window_min_width = 500
    page.horizontal_alignment = 'center'
    page.vertical_alignment = 'center'
    
    texto_login = ft.Container(
        ft.Text(
            value = 'Login',
            size=50,
            weight ='bold'
        ),
        margin = ft.margin.only(left=140)
    )
    
    login_input = ft.Container(
        ft.TextField(
            hint_text = 'Login',
            width = 300,
            border_color = 'white'
        ),
        margin= ft.margin.only(left=50)
    )
    
    senha_input = ft.Container(
        ft.TextField(
            hint_text = 'Password',
            password = True,
            can_reveal_password = True,
            width = 300,
            border_color = 'white'
        ),
        margin= ft.margin.only(left=50)
    )
    
    btn = ft.Container(
        ft.ElevatedButton(
            text = 'Enter',
            width = 200,
            height = 50,
            style = ft.ButtonStyle(
                text_style = ft.TextStyle (
                    size = 30,
                    color = 'white'
                ),
                bgcolor = {
                    ft.MaterialState.DEFAULT: ft.colors.BLACK26,
                    ft.MaterialState.HOVERED: ft.colors.BLACK45
                },
            ),
        ),
        margin = ft.margin.only(left = 100)
    )
    
    layout = ft.Container(
        width = 400,
        height = 400,
        border_radius = 20,
        shadow = ft.BoxShadow(
            blur_radius = 5,
            color = 'black'
        ),
        gradient = ft.LinearGradient(
            begin = ft.alignment.top_left,
            end = ft.alignment.bottom_right,
            colors = [ft.colors.BLACK87,
                      ft.colors.GREY_400,
                      ft.colors.BLACK87],
            stops = [0, 0.5, 1]
        ),
        content = ft.Column(
            spacing = 30,
            alignment = 'center',
            controls = [
                texto_login,
                login_input,
                senha_input,
                btn
            ] 
        )
    )
    
    page.add(layout)

    
ft.app(target = main)