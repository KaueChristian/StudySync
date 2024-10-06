import sqlite3 as sq
import datetime as dt
from src.db.database import Database 

class Agenda:
    def __init__(self):
        self.db = Database()
        self.check_and_create_table()
            
    def check_and_create_table(self):
        
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discipline TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    date_time DATETIME NOT NULL,
                    tier INTEGER NOT NULL CHECK(tier BETWEEN 1 AND 5)
                )                  
            ''')
            conn.commit()

    def add_task(self, discipline: str, subject: str, date_time: str, tier: int):
        if not self.check_table_exists():
            print("A tabela 'tasks' não existe. Por favor, crie uma agenda primeiro.")
            return

        try:
            parsed_date = dt.datetime.strptime(date_time, '%d-%m-%Y')
            date_time_formatted = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            print('Formato de data inválido. Use DD-MM-YYYY.')
            return 

        if not isinstance(tier, int) or tier < 1 or tier > 5:
            print('A prioridade deve ser um número entre 1 e 5.')
            return

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tasks(discipline, subject, date_time, tier)
                    VALUES(?, ?, ?, ?)
                ''', (discipline, subject, date_time_formatted, tier))
                conn.commit()
                print('Tarefa adicionada com sucesso!')
        except sq.IntegrityError as e:
            print(f"Erro de integridade de dados: {e}")
        except sq.DatabaseError as e:
            print(f"Erro no banco de dados: {e}")

    def remove_task(self, id: int):
        if not self.check_table_exists():
            print("A tabela 'tasks' não existe. Por favor, crie uma agenda primeiro.")
            return

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks WHERE id = ?', (id,))
                if cursor.rowcount == 0:
                    print(f"Nenhuma tarefa encontrada com o ID {id}.")
                else:
                    conn.commit()
                    print('A tarefa foi removida com sucesso!')
        except sq.DatabaseError as e:
            print(f"Ocorreu um erro: {e}")
            print("Verifique se a tarefa selecionada existe.")

    def clear_all_tasks(self):
        if not self.check_table_exists():
            print("A tabela 'tasks' não existe. Por favor, crie uma agenda primeiro.")
            return
        
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks")
            task_count = cursor.fetchone()[0]

            if task_count == 0:
                print("Não há tarefas para remover.")
                return

            cursor.execute("DELETE FROM tasks")
            conn.commit()
            print('Todas as tarefas foram removidas com sucesso!')

    def list_tasks(self):
        if not self.check_table_exists():
            print("A tabela 'tasks' não existe. Por favor, crie uma agenda primeiro.")
            return

        with self.db.connect() as conn:
            cursor = conn.cursor()
            try: 
                cursor.execute('SELECT * FROM tasks ORDER BY date_time')
                tasks = cursor.fetchall()
            except sq.OperationalError as e:
                print(f"Erro ao buscar tarefas: {e}")
                return

        if not tasks:
            print("Você não possui nenhuma tarefa. Por favor, crie uma.")
        else:
            print('Todas as suas tarefas:\n')
            for task in tasks:
                id, discipline, subject, date_time, tier = task
                print(f"ID: {id} | Disciplina: {discipline} | Assunto: {subject} | Data: {date_time} | Prioridade: {tier}")

    def remove_table(self):
        if not self.check_table_exists():
            print("Você não possui nenhuma agenda para deletar! Por favor, crie uma.")
            return

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('DROP TABLE tasks')
                conn.commit()
                print('A agenda foi deletada com sucesso!')
        except sq.DatabaseError as e:
            print(f"Ocorreu um erro: {e}")

    def check_table_exists(self) -> bool:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            return cursor.fetchone() is not None

    def update_task(self, id: int, discipline: str = None, subject: str = None, date_time: str = None, tier: int = None):
        if not self.check_table_exists():
            print("A tabela 'tasks' não existe. Por favor, crie uma agenda primeiro.")
            return

        fields = {}
        if discipline:
            fields['discipline'] = discipline
        if subject:
            fields['subject'] = subject
        if date_time:
            try:
                parsed_date = dt.datetime.strptime(date_time, '%d-%m-%Y')
                fields['date_time'] = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                print('ERROR: Formato de data inválido. Use DD-MM-YYYY.')
                return
        if tier:
            if not isinstance(tier, int) or tier < 1 or tier > 5:
                print('A prioridade deve ser um número entre 1 e 5.')
                return
            fields['tier'] = tier

        if not fields:
            print("Nenhum campo para atualizar.")
            return

        set_clause = ', '.join([f"{key} = ?" for key in fields.keys()])
        values = list(fields.values())
        values.append(id)

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(f'UPDATE tasks SET {set_clause} WHERE id = ?', values)
                if cursor.rowcount == 0:
                    print(f"Nenhuma tarefa encontrada com o ID {id}.")
                else:
                    conn.commit()
                    print("Tarefa atualizada com sucesso!")
        except sq.DatabaseError as e:
            print(f"Erro no banco de dados: {e}")
