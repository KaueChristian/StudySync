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
        
    )
    
    login_input = ft.Container(
        ft.TextField(
            hint_text = 'Login',
            width = 300,
            border_color = 'white'
        ),
        
    )
    
    senha_input = ft.Container(
        ft.TextField(
            hint_text = 'Password',
            password = True,
            can_reveal_password = True,
            width = 300,
            border_color = 'white'
        ),
        
    )
    
    btn = ft.Container(
        ft.ElevatedButton(
            text = 'Enter',
            width = 200,
            height = 50,
            style = ft.ButtonStyle(
                color = 'white',
                
                text_style = ft.TextStyle (
                    size = 25
                ),
                bgcolor = {
                    ft.MaterialState.DEFAULT: ft.colors.BLACK26,
                    ft.MaterialState.HOVERED: ft.colors.BLACK45,
                },
            ),
        ),
       
    )
    
    layout = ft.Container(
        width = 600,
        height = 400,
        border_radius = 20,
        shadow = ft.BoxShadow(
            blur_radius = 5,
            color = '#363636'
        ),
        gradient = ft.LinearGradient(
            begin = ft.alignment.top_left,
            end = ft.alignment.bottom_right,
            colors=['#222222', 
                    '#444444',  
                    '#222222'],
            stops = [0, 0.5, 1]
        ),
        content = ft.Column(
            horizontal_alignment = 'center',
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