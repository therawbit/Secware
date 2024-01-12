# database.py
import sqlite3


class DatabaseManager:
    def __init__(self, database_path):
        self.database_path = database_path
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.database_path)
            self.cursor = self.connection.cursor()
            self.cursor.execute(" CREATE TABLE IF NOT EXISTS history ( hash TEXT PRIMARY KEY NOT NULL UNIQUE, name TEXT NOT NULL, date TEXT NOT NULL DEFAULT CURRENT_DATE, size INTEGER NOT NULL, class TEXT );")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def disconnect(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()
            self.connection = None
            self.cursor = None

    def execute_query(self, query, parameters=None):
        self.connect()
        if parameters:
            self.cursor.execute(query, parameters)
        else:
            self.cursor.execute(query)

        results = self.cursor.fetchall()
        self.disconnect()
        return results

    def insert_data(self, data):
        columns = ", ".join(data.keys())
        values = ", ".join("?" for _ in data.values())
        query = f"INSERT INTO history ({columns}) VALUES ({values})"
        self.connect()
        self.cursor.execute(query, list(data.values()))
        self.disconnect()

    def update_data(self, table_name, data, where_clause):
        set_values = ", ".join(f"{key} = ?" for key in data)
        query = f"UPDATE {table_name} SET {set_values} WHERE {where_clause}"
        self.cursor.execute(query, list(data.values()))
        self.connection.commit()

    def fetch_data(self):
        query = "SELECT * FROM history ORDER BY date DESC"
        results = self.execute_query(query)
        return results

    def check_if_exist(self,md5_sum):
        query = "SELECT * FROM history where hash = ?"
        parameter = [md5_sum]
        result = self.execute_query(query,parameter)
        return len(result)==1
