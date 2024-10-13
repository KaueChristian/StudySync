import sqlite3 as sq
import datetime as dt
from src.db.database import Database

class Agenda:
    def __init__(self):
        self.db = Database()
        self.check_and_create_tables()

    def check_and_create_tables(self):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            
            # Criando a tabela de usuários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE
                )
            ''')
            
            # Criando a tabela de tarefas com o relacionamento ao usuário
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tarefas(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    disciplina TEXT NOT NULL,
                    topico TEXT NOT NULL,
                    data DATETIME NOT NULL,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()

    def add_user(self, nome: str, email: str):
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO usuarios (nome, email) VALUES (?, ?)
                ''', (nome, email))
                conn.commit()
                print('Usuário adicionado com sucesso!')
        except sq.IntegrityError as e:
            print(f"Erro de integridade de dados: {e}")
        except sq.DatabaseError as e:
            print(f"Erro no banco de dados: {e}")
            
    def login_user(self, email: str):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM usuarios WHERE = ?', (email))
            user = cursor.fetchone()
            
        if user:
            return user[0]
        else:
            return None

    def add_task(self, usuario_id: int, discipline: str, subject: str, date_time: str):
        if not self.check_table_exists('tarefas'):
            print("A tabela 'tarefas' não existe. Por favor, crie uma agenda primeiro.")
            return

        try:
            parsed_date = dt.datetime.strptime(date_time, '%d-%m-%Y')
            date_time_formatted = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            print('Formato de data inválido. Use DD-MM-YYYY.')
            return

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tarefas(usuario_id, disciplina, topico, data)
                    VALUES(?, ?, ?, ?)
                ''', (usuario_id, discipline, subject, date_time_formatted))
                conn.commit()
                print('Tarefa adicionada com sucesso!')
        except sq.IntegrityError as e:
            print(f"Erro de integridade de dados: {e}")
        except sq.DatabaseError as e:
            print(f"Erro no banco de dados: {e}")

    def remove_task(self, id: int):
        if not self.check_table_exists('tarefas'):
            print("A tabela 'tarefas' não existe. Por favor, crie uma agenda primeiro.")
            return

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tarefas WHERE id = ?', (id,))
                if cursor.rowcount == 0:
                    print(f"Nenhuma tarefa encontrada com o ID {id}.")
                else:
                    conn.commit()
                    print('A tarefa foi removida com sucesso!')
        except sq.DatabaseError as e:
            print(f"Ocorreu um erro: {e}")
            print("Verifique se a tarefa selecionada existe.")

    def clear_all_tasks(self):
        if not self.check_table_exists('tarefas'):
            print("A tabela 'tarefas' não existe. Por favor, crie uma agenda primeiro.")
            return
        
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tarefas")
            task_count = cursor.fetchone()[0]

            if task_count == 0:
                print("Não há tarefas para remover.")
                return

            cursor.execute("DELETE FROM tarefas")
            conn.commit()
            print('Todas as tarefas foram removidas com sucesso!')

    def list_tasks(self, usuario_id: int):
        if not self.check_table_exists('tarefas'):
            print("A tabela 'tarefas' não existe. Por favor, crie uma agenda primeiro.")
            return

        with self.db.connect() as conn:
            cursor = conn.cursor()
            try: 
                cursor.execute('SELECT * FROM tarefas WHERE usuario_id = ? ORDER BY data', (usuario_id,))
                tasks = cursor.fetchall()
            except sq.OperationalError as e:
                print(f"Erro ao buscar tarefas: {e}")
                return

        if not tasks:
            print("Você não possui nenhuma tarefa. Por favor, crie uma.")
        else:
            print('Todas as suas tarefas:\n')
            for task in tasks:
                id, usuario_id, discipline, subject, date_time = task
                print(f"ID: {id} | Disciplina: {discipline} | Assunto: {subject} | Data: {date_time}")

    def remove_table(self):
        if not self.check_table_exists('tarefas'):
            print("Você não possui nenhuma agenda para deletar! Por favor, crie uma.")
            return

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('DROP TABLE tarefas')
                conn.commit()
                print('A agenda foi deletada com sucesso!')
        except sq.DatabaseError as e:
            print(f"Ocorreu um erro: {e}")

    def check_table_exists(self, table_name: str):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return cursor.fetchone() is not None

    def update_task(self, id: int, discipline: str = None, subject: str = None, date_time: str = None):
        if not self.check_table_exists('tarefas'):
            print("A tabela 'tarefas' não existe. Por favor, crie uma agenda primeiro.")
            return

        fields = {}
        if discipline:
            fields['disciplina'] = discipline
        if subject:
            fields['topico'] = subject
        if date_time:
            try:
                parsed_date = dt.datetime.strptime(date_time, '%d-%m-%Y')
                fields['data'] = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                print('ERROR: Formato de data inválido. Use DD-MM-YYYY.')
                return
            
        if not fields:
            print("Nenhum campo para atualizar.")
            return

        set_clause = ', '.join([f"{key} = ?" for key in fields.keys()])
        values = list(fields.values())
        values.append(id)

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(f'UPDATE tarefas SET {set_clause} WHERE id = ?', values)
                if cursor.rowcount == 0:
                    print(f"Nenhuma tarefa encontrada com o ID {id}.")
                else:
                    conn.commit()
                    print("Tarefa atualizada com sucesso!")
        except sq.DatabaseError as e:
            print(f"Erro no banco de dados: {e}")
