import sqlite3 as sq
import datetime as dt
from db.database import Database

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
                    email TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL
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

    def add_user(self, nome: str, email: str, senha: str):
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)
                ''', (nome, email, senha))
                conn.commit()
                user_id = cursor.lastrowid
                print('Usuário adicionado com sucesso!')
                return user_id
        except sq.IntegrityError as e:
            print(f"Erro de integridade de dados: {e}")
        except sq.DatabaseError as e:
            print(f"Erro no banco de dados: {e}")
        return None
            
    def login_user(self, email: str, senha: str):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM usuarios WHERE email = ? AND senha = ?', (email, senha))
            user = cursor.fetchone()
            
            if user:
                return user[0]
            else:
                return None
        
    def verificar_data(self, date_str: str) -> bool:
        try:
            input_date = dt.datetime.strptime(date_str, '%d-%m-%Y')
            today = dt.datetime.today()
            return input_date > today
        except ValueError:
            print("Error: Tipo de data inválido.")
            return False
        
    def add_task(self, discipline: str, subject: str, date_time: str, usuario_id: int):
        
        if not self.check_table_exists('tarefas'):
            print("A tabela 'tarefas' não existe. Por favor, crie uma agenda primeiro.")
            return

        if not self.verificar_data(date_time):
            print("Erro: A data deve ser superior a data atual.")
            return
        
        try:
            parsed_date = dt.datetime.strptime(date_time, '%d-%m-%Y')
            date_time_formatted = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            print('Formato de data inválido. Use DD-MM-YYYY HH:MM:SS.')
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

    def remove_task(self, id: int, id_usuario):
        if not self.check_table_exists('tarefas'):
            print("A tabela 'tarefas' não existe. Por favor, crie uma agenda primeiro.")
            return
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tarefas WHERE id = ? AND usuario_id = ?', (id, id_usuario))
                if cursor.rowcount == 0:
                    print(f"Nenhuma tarefa encontrada com o ID {id}.")
                else:
                    conn.commit()
                    print('A tarefa foi removida com sucesso!')
        except sq.DatabaseError as e:
            print(f"Ocorreu um erro: {e}")
            print("Verifique se a tarefa selecionada existe.")

    def clear_all_tasks(self, usuario_id):
        if not self.check_table_exists('tarefas'):
            print("A tabela 'tarefas' não existe. Por favor, crie uma agenda primeiro.")
            return
        
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tarefas WHERE usuario_id = ?", (usuario_id,))
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

    def remove_table(self, usuario_id):
        if not self.check_table_exists('tarefas'):
            print("Você não possui nenhuma agenda para deletar! Por favor, crie uma.")
            return

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tarefas WHERE usuario_id = ?', (usuario_id,))
                conn.commit()
                print('A agenda foi deletada com sucesso!')
        except sq.DatabaseError as e:
            print(f"Ocorreu um erro: {e}")

    def check_table_exists(self, table_name: str):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return cursor.fetchone() is not None

    def update_task(self, id: int, usuario_id: int, discipline: str = None, subject: str = None, date_time: str = None):
        if not self.check_table_exists('tarefas'):
            print("A tabela 'tarefas' não existe. Por favor, crie uma agenda primeiro.")
            return
        
        if not usuario_id:
            print("O usuario deve ser especificado.")
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
                print('ERROR: Formato de data inválido. Use DD-MM-YYYY HH:MM:SS.')
                return
            
        if not fields:
            print("Nenhum campo para atualizar.")
            return

        set_clause = ', '.join([f"{key} = ?" for key in fields.keys()])
        valores = list(fields.values())
        valores.extend([id, usuario_id])

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(f'UPDATE tarefas SET {set_clause} WHERE id = ? AND usuario_id = ?', valores)
                if cursor.rowcount == 0:
                    print(f"Nenhuma tarefa encontrada com o ID {id}.")
                else:
                    conn.commit()
                    print("Tarefa atualizada com sucesso!")
        except sq.DatabaseError as e:
            print(f"Erro no banco de dados: {e}")

    def get_topico_by_id(self, tarefa_id):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT topico FROM tarefas WHERE id = ?', (tarefa_id,))
            result = cursor.fetchone()
            return result[0] if result else None
