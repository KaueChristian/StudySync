from src.db.funcoes import Agenda

def display_user_menu():
    print('''
        ======== Bem-vindo =========
        1. Registrar Usuário
        2. Login
        0. Sair
        ============================
    ''')

def display_task_menu():
    print('''
        ======== Agenda =========
        1. Adicionar Tarefa
        2. Listar Todas as Tarefas
        3. Remover Tarefa
        4. Atualizar Tarefa
        5. Remover Todas as Tarefas
        6. Remover Agenda
        0. Sair
        =========================
    ''')

def user_menu(option, agenda):
    match option:
        case 1:
            name = input('Nome: ').strip()
            email = input('Email: ').strip()
            user_id = agenda.add_user(name, email)
            if user_id: 
                print(f'Usuário {name} registrado com sucesso!')
            return user_id
        
        case 2:
            email = input('Email: ').strip()
            user_id = agenda.login_user(email)
            if user_id:
                print('Login bem-sucedido!')
            else:
                print('Email não encontrado. Por favor, registre-se primeiro.')
            return user_id
        
        case 0:
            print('Saindo...')
            exit()

        case _:
            print('Opção inválida! Tente novamente.')
            return None
        
        
def task_menu(option, agenda, user_id):
    match option:
        case 1:
            discipline = input('Disciplina: ').strip()
            subject = input('Assunto: ').strip()
            date_time = input('Data (DD-MM-YYYY HH:MM:SS): ').strip()
            agenda.add_task(discipline, subject, date_time, user_id)
        
        case 2:
            agenda.list_tasks(user_id)
        
        case 3:
            id_input = input('Insira o ID da tarefa a ser removida: ').strip()
            if not id_input.isdigit():
                print('ID inválido. Deve ser um número.')
                return
            id = int(id_input)
            agenda.remove_task(id, user_id)
        
        case 4:
            id_input = input('ID da tarefa a ser atualizada: ').strip()
            if not id_input.isdigit():
                print('ID inválido. Deve ser um número.')
                return
            id = int(id_input)
            discipline = input('Nova Disciplina (deixe em branco para não alterar): ').strip()
            subject = input('Novo Assunto (deixe em branco para não alterar): ').strip()
            date_time = input('Nova Data (DD-MM-YYYY, deixe em branco para não alterar): ').strip()
            agenda.update_task(id, user_id, discipline or None, subject or None, date_time)
        
        case 5:
            confirm = input('Tem certeza que deseja remover todas as tarefas? (s/n): ').strip().lower()
            if confirm == 's':
                agenda.clear_all_tasks(user_id)
            else:
                print('Operação cancelada.')
        
        case 6:
            confirm = input('Tem certeza que deseja remover a agenda (todas as tarefas)? (s/n): ').strip().lower()
            if confirm == 's':
                agenda.remove_table(user_id)
            else:
                print('Operação cancelada.')
        
        case 0:
            print('Saindo...')
            exit()
        
        case _:
            print('Opção inválida! Tente novamente.')

def main():
    agenda = Agenda()
    user_id = None
    
    while not user_id:
        display_user_menu()
        try:
            option = int(input('Opção: ').strip())
            user_id = user_menu(option, agenda)
        except ValueError:
            print('Entrada inválida. Por favor, insira um número válido.')
    
    while True:
        display_task_menu()
        try:
            option = int(input('Opção: ').strip())
            task_menu(option, agenda, user_id)
        except ValueError:
            print('Entrada inválida. Por favor, insira um número válido.')

if __name__ == "__main__":
    main()