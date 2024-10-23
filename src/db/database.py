import sqlite3 as sq

class Database:
    def __init__(self, db_name='agenda.db'):
        self.db_name = db_name

    def connect(self):
        try:
            conn = sq.connect(self.db_name)
            return conn
        except sq.Error as e:
            print(f"Error connecting to database? {e}")
            return None
        
    def create_table(self):
        conn = self.connect()
        if conn:
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