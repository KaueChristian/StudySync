import sqlite3 as sq
import datetime as dt
import src.database as Database

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
                tier INTEGER NOT NULL
                )                  
            ''')
            conn.commit()

    def add_task(self, discipline, subject, date_time, tier):
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("The table 'tasks' does not exist. Please create an agenda first.")
            conn.close()
            return

        try:
            dt.datetime.strptime(date_time, '%d-%m-%Y')
        except ValueError:
            print('Invalid date format. Use DD-MM-YYYY.')
            conn.close()
            return 
        if not tier.isdigit() or int(tier) < 1 or int(tier) > 5:
            print('Priority must be a number between 1 and 5.')
            conn.close()
            return
        
        try:
            cursor.execute('''
                INSERT INTO tasks(discipline, subject, date_time, tier)
                VALUES(?, ?, ?, ?)
                ''', (discipline, subject, date_time, tier)
            )
            conn.commit()
            print('Task added successfully!')
        except sq.IntegrityError as e:
            print(f"Data integrity error: {e}")
        except sq.DatabaseError as e:
            print(f"Database error: {e}")
        finally:
            conn.close()
        
    def remove_task(self, id):
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            table_exists = cursor.fetchone()

            if not table_exists:
                print("The table 'tasks' does not exist. Please create an agenda first.")
                return
        
            cursor.execute('DELETE FROM tasks WHERE id = ?', (id,))

            if cursor.rowcount == 0:
                print(f"No task found with id {id}.")
            else:
                conn.commit()
                print('The task has been removed successfully!')
        except sq.DatabaseError as e:
            print(f"An error occurred: {e}")
            print("Verify if the selected task exists.")
        finally:
            conn.close()
    
    def clear_all_tasks(self):
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("The table 'tasks' does not exist. Please create an agenda first.")
            conn.close()
            return
        
        cursor.execute("SELECT COUNT(*) FROM tasks")
        task_count = cursor.fetchone()[0]

        if task_count == 0:
            print("There are no tasks to remove.")
            conn.close()
            return

        cursor.execute("DELETE FROM tasks")
        conn.commit()
        conn.close()
        print('All tasks removed successfully!')

    def list_task(self):
        conn = self.db.connect()
        cursor = conn.cursor()

        try: 
            cursor.execute('SELECT * FROM tasks')
            tasks = cursor.fetchall()
        except sq.OperationalError as e:
            print(f"Error fetching tasks: {e}")
            return

        print('All your tasks: \n')

        if not tasks:
            print("You don't have any task. Please create it.")
        else:
            for task in tasks:
                print(task)
        
        conn.close()
        
    def create_tb(self):
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discipline TEXT NOT NULL,
            subject TEXT NOT NULL,
            date_time DATETIME NOT NULL,
            tier INTEGER NOT NULL
            )                  
        ''')
        
        conn.commit()
        conn.close()

        print('Your agenda has been created with successfully!')

    def remove_tb(self):
        conn = self.db.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            table_exists = cursor.fetchone()

            if table_exists:
                cursor.execute('DROP TABLE tasks')
                msg = 'The agenda has been deleted with successfully!'
            else:
                msg = "You don't have any agendas for delete! Please create a one"
        
            print(msg)
        except sq.DatabaseError as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()

    def check_table_exists(self):
        conn = self.db.connect()
        
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        table_exists = cursor.fetchone() is not None
        conn.close()
        
        return table_exists