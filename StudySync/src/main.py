from src.agenda import Agenda
from src.database import Database
import sqlite3 as sq
import datetime as dt


agenda = Agenda()

def check_table_exists():
    return agenda.check_table_exists()

def display_menu():
    
    print('''
        1. Create agenda
        2. Delete agenda
        3. Add a task
        4. List all tasks
        5. Remove a task
        6. Remove all tasks
        0. Exit
    ''')

def menu(option):
    match option:
        case 1:
            agenda.create_tb()
        case 2:
            agenda.remove_tb()
        case 3:
            if agenda.check_table_exists():
                discipline = input('Discipline: ')
                subject = input('Subject: ')
                date_time = (input('Date and time (YYYY-MM-DD): '))
                tier = input('Tier/Prioriry: ')
                agenda.add_task(discipline, subject, date_time, tier)
            else:
                print("You don't have any agenda. Please create one.")
        case 4:
            agenda.list_task()
        case 5:
            id = input('Insert the id of a task: ')
            agenda.remove_task(id)
        case 6:
            agenda.clear_all_tasks()
        case 0:
            print('Exiting...')
            exit()
        case _:
            print('Invalid option! Try again')

if __name__ == "__main__":
    while True:
        display_menu()
        try:
            option = int(input('Option: '))
            menu(option)
        except ValueError:
            print('Invalid input. Please enter with a number option')
    

