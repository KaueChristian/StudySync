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