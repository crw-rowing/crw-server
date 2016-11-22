import psycopg2

class UserDatabase:
    def __init__(self, database_name, database_user):
        self.database_connection = psycopg2.connect(database=database_name,
                                             user=database_user)
        self.cursor = self.database_connection.cursor()

    def init_database(self):
        self.cursor.execute(
            """CREATE TABLE users (id INTEGER, email TEXT,
            password TEXT);""")
        self.database_connection.commit()

    def add_user(self, email, password):
        self.cursor.execute(
            """SELECT id FROM users;""");
        ids = self.cursor.fetchall()
        max_id = 0
        for userid in ids:
            max_id = max(userid[0], max_id)
        self.cursor.execute(
            """INSERT INTO users (id, email, password) VALUES
            (%s, %s, %s);""", (max_id + 1, email, password))

