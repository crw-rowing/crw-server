import psycopg2
from passlib.context import CryptContext

# Global password context
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"]
    )


class BaseDatabase:
    def __init__(self, database_name, database_user):
        self.database_connection = psycopg2.connect(database=database_name,
                                                    user=database_user)
        self.cursor = self.database_connection.cursor()

    def init_database(self):
        """Creates the table structure in the database.  This is to be used
        once for every database, not on every restart of the program."""
        self.cursor.execute(
            """CREATE TABLE teams
            (id INTEGER PRIMARY KEY,
            name TEXT NOT NULL)""")
        self.cursor.execute(
            """CREATE TABLE users
            (id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            team_id INTEGER REFERENCES teams(id),
            coach BOOLEAN);""")
        self.database_connection.commit()

    def drop_all_tables(self):
        """Drops all tables from the database"""
        self.cursor.execute(
            """DROP TABLE users;""")
        self.cursor.execute(
            """DROP TABLE teams""")
        self.database_connection.commit()

    def close_database_connection(self):
        """Closes the database_connection and the cursor"""
        self.cursor.close()
        self.database_connection.close()


class UserDatabase(BaseDatabase):
    def add_user(self, email, password):
        """Adds an user to the database, using the given email as
        email, the given password as password and a new id, one higher
        than the highest id in the database."""

        # Check if there isn't already an user with this email address
        self.cursor.execute(
            """SELECT email FROM users
            WHERE email = %s;""", (email,))
        if self.cursor.fetchone() is not None:
            raise ValueError('An user with this email (' + email +
                             ') already exists')

        # Find the current max_id to generate a new id that is one
        # higher
        self.cursor.execute(
            """SELECT MAX(id) FROM users;""")
        (max_id,) = self.cursor.fetchone()
        if max_id is None:
            max_id = 0

        # Hash and salt the password using passlib
        password_hash = pwd_context.hash(password)

        self.cursor.execute(
            """INSERT INTO users (id, email, password) VALUES
            (%s, %s, %s);""", (max_id + 1, email, password_hash))
        self.database_connection.commit()

    def verify_user(self, email, password):
        """Returns whether the given password is the same as the
        password associated with this email address. """
        self.cursor.execute(
            """SELECT password FROM users
            WHERE email = %s;""", (email,))

        saved_password_tuple = self.cursor.fetchone()
        if saved_password_tuple is None:
            raise ValueError('There is no user associated with ' +
                             'this email address')
        saved_password_hash = saved_password_tuple[0]

        return pwd_context.verify(password, saved_password_hash)

    def get_user_id(self, email):
        """Returns the user_id associated with this email address"""
        self.cursor.execute(
            """SELECT id FROM users
            WHERE email = %s;""", (email,))

        saved_id_tuple = self.cursor.fetchone()
        if saved_id_tuple is None:
            raise ValueError('There is no user associated with ' +
                             'this email address')

        return saved_id_tuple[0]
