# main.py

from src.db.funcoes import Agenda

def display_menu():
    print('''
        ======== Agenda ========
        1. Adicionar Tarefa
        2. Listar Todas as Tarefas
        3. Remover Tarefa
        4. Atualizar Tarefa
        5. Remover Todas as Tarefas
        6. Remover Agenda
        0. Sair
        =========================
    ''')

def menu(option, agenda):
    match option:
        case 1:
            discipline = input('Disciplina: ').strip()
            subject = input('Assunto: ').strip()
            date_time = input('Data (DD-MM-YYYY): ').strip()
            tier_input = input('Prioridade (1-5): ').strip()
            if not tier_input.isdigit():
                print('Prioridade inválida. Deve ser um número entre 1 e 5.')
                return
            tier = int(tier_input)
            agenda.add_task(discipline, subject, date_time, tier)
        
        case 2:
            agenda.list_tasks()
        
        case 3:
            id_input = input('Insira o ID da tarefa a ser removida: ').strip()
            if not id_input.isdigit():
                print('ID inválido. Deve ser um número.')
                return
            id = int(id_input)
            agenda.remove_task(id)
        
        case 4:
            id_input = input('ID da tarefa a ser atualizada: ').strip()
            if not id_input.isdigit():
                print('ID inválido. Deve ser um número.')
                return
            id = int(id_input)
            discipline = input('Nova Disciplina (deixe em branco para não alterar): ').strip()
            subject = input('Novo Assunto (deixe em branco para não alterar): ').strip()
            date_time = input('Nova Data (DD-MM-YYYY, deixe em branco para não alterar): ').strip()
            tier_input = input('Nova Prioridade (1-5, deixe em branco para não alterar): ').strip()
            tier = int(tier_input) if tier_input.isdigit() else None
            agenda.update_task(id, discipline or None, subject or None, date_time or None, tier)
        
        case 5:
            confirm = input('Tem certeza que deseja remover todas as tarefas? (s/n): ').strip().lower()
            if confirm == 's':
                agenda.clear_all_tasks()
            else:
                print('Operação cancelada.')
        
        case 6:
            confirm = input('Tem certeza que deseja remover a agenda (todas as tarefas)? (s/n): ').strip().lower()
            if confirm == 's':
                agenda.remove_table()
            else:
                print('Operação cancelada.')
        
        case 0:
            print('Saindo...')
            exit()
        
        case _:
            print('Opção inválida! Tente novamente.')

def main():
    agenda = Agenda()
    
    while True:
        display_menu()
        try:
            option = int(input('Opção: ').strip())
            menu(option, agenda)
        except ValueError:
            print('Entrada inválida. Por favor, insira um número válido.')

if __name__ == "__main__":
    main()
